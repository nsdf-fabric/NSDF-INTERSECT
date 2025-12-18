package main

import (
	"context"
	"fmt"
	"math"
	"math/rand"
	"time"

	"dagger/nsdf-intersect-ci/internal/dagger"
)

type NsdfIntersectCi struct{}

// Build the test environment for UV
func (m *NsdfIntersectCi) BuildTestEnv(
	// +defaultPath="/services/nsdf_intersect_dashboard"
	source *dagger.Directory) *dagger.Container {
	return dag.Container().From("python:3.10-slim").
		WithDirectory("/src", source, dagger.ContainerWithDirectoryOpts{Exclude: []string{".venv", "dist"}}).
		WithExec([]string{"pip", "install", "uv"}).
		WithWorkdir("/src").
		WithExec([]string{"uv", "sync", "--all-groups"})
}

// Runs dashboard tests
func (m *NsdfIntersectCi) TestDashboard(
	ctx context.Context,
	// +defaultPath="/services/nsdf_intersect_dashboard"
	source *dagger.Directory) (string, error) {
	return m.BuildTestEnv(source).WithExec([]string{"uv", "run", "pytest"}).Stdout(ctx)
}

// Build container from Dockerfile
func (m *NsdfIntersectCi) BuildFromDockerfile(source *dagger.Directory, version string, sha string) *dagger.Container {
	return dag.Container().Build(source, dagger.ContainerBuildOpts{
		BuildArgs: []dagger.BuildArg{
			dagger.BuildArg{Name: "GIT_SHA", Value: sha},
			dagger.BuildArg{Name: "VERSION", Value: version},
		},
	}).WithLabel("org.opencontainers.image.created", time.Now().UTC().Format(time.RFC3339))
}

// Publish Docker image to registry
func (m *NsdfIntersectCi) PublishImage(ctx context.Context, name string,
	// +optional
	versions []string,
	sha string,
	// +default="ttl.sh"
	registry string,
	username string,
	password *dagger.Secret,
	// +defaultPath="services"
	source *dagger.Directory,
) ([]string, error) {

	if len(versions) == 0 {
		versions = append(versions, "latest")
	}

	published := make([]string, len(versions))

	for i, version := range versions {
		container := &dagger.Container{}
		switch name {
		case "intersect-dashboard":
			container = m.BuildFromDockerfile(source.Directory("nsdf_intersect_dashboard"), version, sha)
		case "intersect-service":
			container = m.BuildFromDockerfile(source.Directory("nsdf_intersect_service"), version, sha)
		case "intersect-storage":
			container = m.BuildFromDockerfile(source.Directory("ndsf_intersect_storage"), version, sha)
		}

		imageName := fmt.Sprintf("%s/%s/%s:%s", registry, username, name, version)
		if registry != "ttl.sh" {
			container = container.WithRegistryAuth(registry, username, password)
		} else {
			imageName = fmt.Sprintf("%s/%s-%.0f", registry, name, math.Floor(rand.Float64()*10000000))
		}

		if _, err := container.Publish(ctx, imageName); err != nil {
			return nil, err
		}

		published[i] = imageName
	}

	return published, nil
}
