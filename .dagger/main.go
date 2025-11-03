package main

import (
	"context"
	"fmt"
	"math"
	"math/rand"

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
func (m *NsdfIntersectCi) BuildFromDockerfile(source *dagger.Directory) *dagger.Container {
	return dag.Container().Build(source)
}

// Builds dashboard container
func (m *NsdfIntersectCi) BuildDashboardContainer(
	// +defaultPath="services/nsdf_intersect_dashboard"
	source *dagger.Directory,
) *dagger.Container {
	return m.BuildFromDockerfile(source)
}

// Builds service container
func (m *NsdfIntersectCi) BuildServiceContainer(
	// +defaultPath="services/nsdf_intersect_service"
	source *dagger.Directory,
) *dagger.Container {
	return m.BuildFromDockerfile(source)
}

// Builds service container
func (m *NsdfIntersectCi) BuildStorageContainer(
	// +defaultPath="services/nsdf_intersect_storage"
	source *dagger.Directory,
) *dagger.Container {
	return m.BuildFromDockerfile(source)
}

// Publish Docker image to registry
func (m *NsdfIntersectCi) PublishImage(ctx context.Context, name string,
	// +default="latest"
	tag string,
	// +default="ttl.sh"
	registry string,
	username string,
	password *dagger.Secret,
	// +defaultPath="services"
	source *dagger.Directory,
) (string, error) {

	container := &dagger.Container{}
	switch name {
	case "intersect-dashboard":
		container = m.BuildDashboardContainer(source.Directory("nsdf_intersect_dashboard"))
	case "intersect-service":
		container = m.BuildServiceContainer(source.Directory("nsdf_intersect_service"))
	case "intersect-storage":
		container = m.BuildStorageContainer(source.Directory("ndsf_intersect_storage"))
	}

	if registry != "ttl.sh" {
		container.WithRegistryAuth(registry, username, password)
		return container.Publish(ctx, fmt.Sprintf("%s/%s/%s:%s", registry, username, name, tag))
	} else {
		return container.Publish(ctx, fmt.Sprintf("%s/%s-%.0f", registry, name, math.Floor(rand.Float64()*10000000)))
	}
}
