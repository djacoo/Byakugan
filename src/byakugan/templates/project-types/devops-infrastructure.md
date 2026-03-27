# DevOps / Infrastructure — Working Standards

## What This Project Type Demands
Infrastructure mistakes have blast radii. A bad deploy can take down production for thousands of users. A misconfigured security group can expose a database to the internet. Infrastructure changes must be reviewed, tested, and applied with the same rigor as production code — more rigor, in fact, because the failure modes are often silent until they are catastrophic.

## Before Starting Any Change
- Understand the current state before proposing changes. Read existing IaC code, check the current configuration, and run `terraform plan` / `pulumi preview` before writing anything new.
- Identify the blast radius of the change: what services are affected if this goes wrong?
- Determine if the change requires downtime. If it does, plan a maintenance window and notify stakeholders.
- Identify state that must be preserved (databases, queues, S3 buckets). Flag anything that risks data loss.
- Check whether the change needs to be rolled back — define the rollback procedure before applying.

## Architecture Standards
- All infrastructure defined as code in version control. No manual changes to production. Ever.
- One environment per state file: never share Terraform state between production and non-production.
- Secrets managed by a secrets manager (Vault, AWS Secrets Manager, GCP Secret Manager). No secrets in IaC code, environment variables in plain text, or CI/CD logs.
- Use modules for reusable infrastructure patterns. Never copy-paste resource blocks.
- Tag every resource: `environment`, `team`, `project`, `managed-by`.
- Use remote state with locking for all Terraform workspaces.

## How to Approach Any Task
1. Read the existing IaC code fully before modifying. Understand what currently exists.
2. Make the smallest change that achieves the goal. Avoid bundling unrelated changes.
3. Run `terraform plan` / `pulumi preview` and review the diff carefully before applying. Look for unexpected deletions or replacements.
4. Apply to non-production first. Verify the change produces the expected behavior.
5. Apply to production with a monitoring window. Watch metrics and logs for anomalies after the change.

## Non-Negotiable Rules
- No manual changes to infrastructure managed by IaC. If you make a manual change in an emergency, immediately codify it.
- No secrets in code, config files, or state files. Secrets go in a secrets manager.
- Security groups and firewall rules follow least privilege. No `0.0.0.0/0` ingress without explicit justification and approval.
- Encryption at rest on all databases and object storage. No exceptions.
- Public access explicitly blocked on all storage buckets unless the purpose is to serve public content.
- Log retention configured on all log groups with a defined retention period.
- Backup policies configured on all stateful resources (databases, queues, critical buckets).
- Policy-as-code (`tfsec`, `checkov`, OPA) runs in CI and blocks PRs with violations.

## Change Safety Rules
Before any production infrastructure change:
- [ ] `terraform plan` output reviewed — no unexpected resource deletions or replacements.
- [ ] Change applied to staging first and verified.
- [ ] Rollback procedure documented and tested.
- [ ] Monitoring and alerts checked before the change window.
- [ ] Stakeholders notified if the change may cause service interruption.

High-risk operations requiring explicit approval:
- Any change to a production database (schema, config, instance type, encryption).
- Any change to network ACLs, security groups, or firewall rules.
- Any change to IAM roles or policies.
- Any change to backup or replication configuration.
- Any resource deletion in production.

## Observability Standards
Every deployed service must have:
- Health check endpoint.
- CPU, memory, error rate, and latency metrics.
- Structured logs with correlation IDs.
- Alerts configured for: error rate > threshold, latency p95 > threshold, health check failure.

SLOs defined for every production service:
- Availability target (e.g., 99.9%).
- Latency target (e.g., p95 < 500ms).
- Error budget burn rate alerts.

## Definition of Done
- [ ] IaC code reviewed by at least one other engineer.
- [ ] `terraform plan` output shows only the intended changes.
- [ ] Policy-as-code checks pass (`tfsec`/`checkov` clean).
- [ ] Change applied to staging and verified.
- [ ] No hardcoded secrets in any IaC or config file.
- [ ] Encryption at rest enabled on all new databases and storage.
- [ ] Security groups follow least privilege.
- [ ] All new resources tagged with required tags.
- [ ] Monitoring and alerting configured for new services.
- [ ] Rollback procedure documented.
