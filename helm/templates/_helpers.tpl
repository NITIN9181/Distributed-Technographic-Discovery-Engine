{{/*
Common labels for all resources.
*/}}
{{- define "techdetector.labels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end }}

{{/*
Selector labels for matching pods.
*/}}
{{- define "techdetector.selectorLabels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Full image name with tag.
*/}}
{{- define "techdetector.crawlerImage" -}}
{{ .Values.image.repository }}/crawler:{{ .Values.image.tag }}
{{- end }}

{{- define "techdetector.workerImage" -}}
{{ .Values.image.repository }}/worker:{{ .Values.image.tag }}
{{- end }}
