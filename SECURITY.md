\# Security Policy



\## Project status



AgentOps Governance \& Assurance Control Plane is under active development.



The current release is intended for development, demonstration and portfolio

use. It must not be treated as the sole security boundary for production AI

agents without additional security controls.



\## Supported versions



| Version | Supported |

|---|---|

| Latest commit on `main` | Yes |

| Older commits | No |

| Unreleased local changes | No |



Security fixes are applied only to the latest version on the `main` branch.



\## Reporting a vulnerability



Please do not disclose security vulnerabilities through a public GitHub issue,

discussion, pull request or social-media post.



To report a vulnerability:



1\. Open the repository's \*\*Security\*\* tab.

2\. Select \*\*Report a vulnerability\*\* if private vulnerability reporting is enabled.

3\. Provide enough information to reproduce and assess the problem.

4\. Remove credentials, personal information and production data from all evidence.



If private reporting is unavailable, contact the repository owner privately

through the contact information shown on their GitHub profile.



\## Information to include



A useful report should contain:



\- A clear description of the vulnerability

\- The affected endpoint, module or control

\- Steps required to reproduce it

\- Expected and actual behaviour

\- Potential confidentiality, integrity or availability impact

\- A minimal proof of concept, when safe

\- Suggested remediation, if known

\- Whether the vulnerability has been disclosed elsewhere



\## Security response process



Reported vulnerabilities will be handled using the following process:



1\. Acknowledge the report.

2\. Reproduce and validate the issue.

3\. Determine severity and affected components.

4\. Develop and test a correction.

5\. Release the correction.

6\. Publish an advisory when appropriate.



\## Security boundaries



The current project does not yet provide production-ready implementations of:



\- User authentication

\- Role-based access control

\- Transport-layer security termination

\- Rate limiting

\- Distributed secret management

\- Tamper-evident external audit storage

\- Database encryption and managed backups

\- Network or workload isolation

\- Production monitoring and alerting



Deployments must provide these controls outside or around the application.



\## Threat model



The control plane should assume that:



\- Agent-supplied manifests may be malformed or malicious

\- Agent identities may be impersonated

\- API clients may attempt unauthorised lifecycle changes

\- Policy inputs may try to bypass validation

\- Approval records may be targeted for modification

\- Sensitive information may appear in request payloads

\- Dependencies may contain vulnerabilities

\- Audit evidence may be deleted or altered



\## Security principles



The project follows these principles:



\- Deny invalid requests

\- Validate all external input

\- Apply least privilege

\- Keep human approval explicit

\- Separate policy authors from approvers

\- Preserve governance evidence

\- Avoid secrets in source code

\- Return minimal error information

\- Keep dependencies reviewed and updated

\- Record security-relevant state changes



\## Sensitive information



Never commit:



\- API keys

\- Passwords

\- Access tokens

\- Private keys

\- Connection strings containing credentials

\- Real customer information

\- Production agent prompts containing confidential data

\- Unredacted governance or audit evidence



Use environment variables or an approved secret-management system.



\## Scope



Security reports concerning these areas are in scope:



\- Manifest-validation bypass

\- Agent-registration impersonation

\- Unauthorised agent suspension, reinstatement or retirement

\- Governance-policy bypass

\- Approval-workflow bypass

\- Audit-record manipulation

\- Sensitive-data exposure

\- Injection vulnerabilities

\- Unsafe database operations

\- Dependency vulnerabilities affecting this application



\## Out of scope



The following are normally outside the project's current security scope:



\- Denial-of-service testing against public infrastructure

\- Social-engineering attacks

\- Physical attacks

\- Findings that require previously compromised administrator access

\- Automated scanner reports without reproducible evidence

\- Vulnerabilities in unrelated third-party services



\## Safe testing



Security research must:



\- Use locally controlled test data

\- Avoid accessing another person's information

\- Avoid disrupting services

\- Avoid destructive payloads

\- Stop immediately if unexpected sensitive data is exposed

\- Preserve evidence without publishing confidential details



Thank you for helping improve the security of this project.

