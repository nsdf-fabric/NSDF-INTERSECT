{{/*
Return the proper dashboard image name (Service)
*/}}
{{- define "nsdf-intersect-dashboard.dashboard.image" -}}
{{- include "common.images.image" (dict "imageRoot" .Values.dashboard.image "global" .Values.global) -}}
{{- end -}}

{{/*
Return the proper dashboard service image name (Service)
*/}}
{{- define "nsdf-intersect-dashboard.dashboardService.image" -}}
{{- include "common.images.image" (dict "imageRoot" .Values.dashboardService.image "global" .Values.global) -}}
{{- end -}}

{{/*
Return the proper storage image name (Service)
*/}}
{{- define "nsdf-intersect-dashboard.storageService.image" -}}
{{- include "common.images.image" (dict "imageRoot" .Values.storageService.image "global" .Values.global) -}}
{{- end -}}

{{/*
Return the proper Container Image Registry secret names
*/}}
{{- define "nsdf-intersect-dashboard.imagePullSecrets" -}}
{{- include "common.images.renderPullSecrets" (dict "images" ( concat (list .Values.dashboard.image .Values.dashboardService.image .Values.storageService.image) ) "context" $) -}}
{{- end -}}


{{/*
Create the name of the service account to use
*/}}
{{- define "nsdf-intersect-dashboard.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
    {{ default (include "common.names.fullname" .) .Values.serviceAccount.name }}
{{- else -}}
    {{ default "default" .Values.serviceAccount.name }}
{{- end -}}
{{- end -}}

{{/*
Return true if cert-manager required annotations for TLS signed certificates are set in the Ingress annotations
Ref: https://cert-manager.io/docs/usage/ingress/#supported-annotations
*/}}
{{- define "nsdf-intersect-dashboard.ingress.certManagerRequest" -}}
{{ if or (hasKey . "cert-manager.io/cluster-issuer") (hasKey . "cert-manager.io/issuer") }}
    {{- true -}}
{{- end -}}
{{- end -}}
