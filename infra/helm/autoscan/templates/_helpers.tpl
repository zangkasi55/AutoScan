{{- define "autoscan.image" -}}
{{- $reg := .Values.image.registry -}}
{{- if $reg -}}{{ $reg }}/{{- end -}}autoscan/{{ .component }}:{{ .Values.image.tag }}
{{- end -}}

{{- define "autoscan.labels" -}}
app.kubernetes.io/name: autoscan
app.kubernetes.io/component: {{ .component }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: helm
{{- if .Values.workloadIdentity.enabled }}
azure.workload.identity/use: "true"
{{- end }}
{{- end -}}
