variable "name" { type = string }
variable "environment" { type = string }
variable "retention_in_days" { type = number }
variable "log_groups" { type = list(string) }
