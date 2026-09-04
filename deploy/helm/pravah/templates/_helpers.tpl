{{/*
Expand the name of the chart.
*/}}
{{- define "pravah.name" -}}
{{- default .Chart.Name .Values.global.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
*/}}
{{- define "pravah.fullname" -}}
{{- if .Values.global.fullnameOverride }}
{{- .Values.global.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.global.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "pravah.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels applied across all workloads
*/}}
{{- define "pravah.labels" -}}
helm.sh/chart: {{ include "pravah.chart" . }}
app.kubernetes.io/name: {{ include "pravah.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: pravah-platform
{{- end }}

{{/*
Selector labels for API
*/}}
{{- define "pravah.apiSelectorLabels" -}}
app.kubernetes.io/name: {{ include "pravah.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: api
{{- end }}

{{/*
Selector labels for Web
*/}}
{{- define "pravah.webSelectorLabels" -}}
app.kubernetes.io/name: {{ include "pravah.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: web
{{- end }}

{{/*
Selector labels for Scheduler
*/}}
{{- define "pravah.schedulerSelectorLabels" -}}
app.kubernetes.io/name: {{ include "pravah.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: scheduler
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "pravah.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "pravah.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Resolve Image full path
*/}}
{{- define "pravah.apiImage" -}}
{{- $registry := default "ghcr.io" .Values.global.imageRegistry }}
{{- printf "%s/%s:%s" $registry .Values.api.image.repository (default .Chart.AppVersion .Values.api.image.tag) }}
{{- end }}

{{- define "pravah.webImage" -}}
{{- $registry := default "ghcr.io" .Values.global.imageRegistry }}
{{- printf "%s/%s:%s" $registry .Values.web.image.repository (default .Chart.AppVersion .Values.web.image.tag) }}
{{- end }}
