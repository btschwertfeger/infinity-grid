{{/*
Expand the name of the chart.
*/}}
{{- define "infinity-grid.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "infinity-grid.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
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
{{- define "infinity-grid.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "infinity-grid.labels" -}}
helm.sh/chart: {{ include "infinity-grid.chart" . }}
{{ include "infinity-grid.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "infinity-grid.selectorLabels" -}}
app.kubernetes.io/name: {{ include "infinity-grid.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create database connection details
*/}}
{{- define "infinity-grid.database.host" -}}
{{- .Values.database.host -}}
{{- end -}}

{{- define "infinity-grid.database.port" -}}
{{- .Values.database.port | default 5432 -}}
{{- end -}}

{{- define "infinity-grid.database.database" -}}
{{- .Values.database.database -}}
{{- end -}}

{{- define "infinity-grid.database.username" -}}
{{- .Values.database.username -}}
{{- end -}}

{{- define "infinity-grid.database.password" -}}
{{- .Values.database.password -}}
{{- end -}}

{{/*
Create the database secret name
*/}}
{{- define "infinity-grid.databaseSecretName" -}}
{{- include "infinity-grid.fullname" . -}}-db
{{- end -}}

{{/*
Get the database password key
*/}}
{{- define "infinity-grid.databasePasswordKey" -}}
password
{{- end -}}

{{/*
Get the database username key
*/}}
{{- define "infinity-grid.databaseUsernameKey" -}}
username
{{- end -}}
