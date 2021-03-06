# Creating a stable release
Outlines the processes for publishing a new Charmed Kubernetes release.

## Stable Release Process

### How to read this document

Each step in the release process contains information pertaining to the
description of the jobs and what is required if needing to run the jobs
locally.

Each step should contain the following:

- Job name as seen in jenkins
- Requirements to run the job including what environment variables need to be set
- Example of running the OGC specification within tox.

### Submit PR's to bundle and charms to pin snap version

We need to make sure that the bundle fragments and kubernetes-worker/master
are set to `<k8sver>/stable` prior to cutting a new release.

### Tag existing stable branches with the current stable bundle

For all charm repos that make up CK tag the existing stable branches with
the most recently released stable bundle revision.

_Jenkins Job_: sync-stable-tag-bundle-rev

_Requires_:

To run this manually, the **CDKBOT** Github SSH creds are required and
should be loaded into your ssh-agent.

**Environment Variables**:

- TOX_WORK_DIR=~/.tox

_Example_:

```
tox -e py36 -- ogc --spec jobs/sync-upstream/spec.yml -t tag-stable-rev
```

### Rebase stable on top of master git branches

Once all repositories are tagged we need to rebase what's in master git on
to stable as this will be our snapshot on what we test and subsequently
promote to stable.

_Jenkins Job_: cut-stable-release

_Requires_:

To run this manually, the **CDKBOT** Github SSH creds are required and
should be loaded into your ssh-agent.

**Environment Variables**:

- TOX_WORK_DIR=~/.tox

_Example_:

```
tox -e py36 -- ogc --spec jobs/sync-upstream/spec.yml -t cut-stable-release
```

### Bump snap version to next minor release

Once the rebase has occurred we need to bump the charms and bundle fragments
to the next k8s minor version, ie 1.17/edge.

### Build new CK Charms from stable git branches

Pull down all layers and checkout their stable branches. From there build
each charm against those local branches. After the charms are built they need to be
promoted to the **beta** channel in the charmstore.

>-
  **Note**: Beta channel is required as any bugfix releases happening at the
  same time will use the candidate channels for staging those releases.

_Jenkins Job_: build-charms

_Requires_:

Must be logged into the charmstore as **cdkbot**

**Environment Variables**:

- TOX_WORK_DIR=~/.tox
- CHARM_LIST=jobs/includes/charm-support-matrix.inc
- CHARM_BRANCH=stable
- TO_CHANNEL=beta
- RESOURCE_SPEC=jobs/build-charms/resource-spec.yaml
- FILTER_BY_TAG=k8s
- LAYER_INDEX=https://charmed-kubernetes.github.io/layer-index/
- LAYER_LIST=jobs/build-charms/charm-layer-list.yaml
- LAYER_BRANCH=stable

_Example_:

```
tox -e py36 -- ogc --spec jobs/release/release-spec.yml -t build-charms
```

### Promote new K8S snaps

Promote new K8S snaps for the upcoming stable release to the beta and
candidate channels of the snapstore.

>-
  This is typically handled already by a daily job that will automatically
  push any new stable release to the appropriate channels. If that's the
  case this job will just check for existence and continue on.

_Jenkins Job_: build-snaps

_Requires_:

Must have username/password for **cdkbot** to publish to snapstore.

**Environment Variables**:

- TOX_WORK_DIR=~/.tox
- SNAP_LIST=jobs/includes/k8s-snap-list.inc
- K8STEAMCI_USR=snapstore-user
- K8STEAMCI_PSQ=snapstore-password

_Example_:

```
tox -e py36 -- ogc --spec jobs/build-snaps/spec.yml -t sync
```

### Validate Charmed Kubernetes

With all bits in place, time to validate CK.

_Jenkins Job_: validate-ck

_Requires_:

Must have aws credentials setup and loaded within Juju credentials.

**Environment Variables**:

- INTEGRATION_TEST_PATH=jobs/integration
- JUJU_DEPLOY_CHANNEL=beta

_Example_:

```
tox -e py36 -- ogc --spec validate/spec.yml
```

### Validate CK Upgrade

Run validation tests against minor to minor upgrades, for example, 1.13 ->
1.16, 1.14 -> 1.16, 1.15 > 1.16

_Jenkins Job_: validate-ck-upgrade

_Requires_:

Must have aws credentials setup and loaded within Juju credentials.

**Environment Variables**:

- INTEGRATION_TEST_PATH=jobs/integration
- JUJU_DEPLOY_CHANNEL=beta

_Example_:

```
tox -e py36 -- ogc --spec validate/upgrade-spec.yml
```

### Validate CK ARM64

Run validation tests on a arm64 deployment

_Jenkins Job_: validate-ck-arm64

_Requires_:

Must have aws credentials setup and loaded within Juju credentials.

**Environment Variables**:

- INTEGRATION_TEST_PATH=jobs/integration
- JUJU_DEPLOY_CHANNEL=beta

_Example_:

```
tox -e py36 -- ogc --spec validate/ck-arm-spec.yml
```

### Validate CK with Calico

Run validation tests on CK with Calico enabled

_Jenkins Job_: validate-ck-calico

_Requires_:

Must have aws credentials setup and loaded within Juju credentials.

**Environment Variables**:

- INTEGRATION_TEST_PATH=jobs/integration
- JUJU_DEPLOY_CHANNEL=beta

_Example_:

```
tox -e py36 -- ogc --spec validate/calico-spec.yml
```

### Validate CK with Tigera Secure EE

Run validation tests on CK with Tigera Secure EE enabled

_Jenkins Job_: validate-ck-tigera-secure-ee

_Requires_:

Must have aws credentials setup and loaded within Juju credentials.

**Environment Variables**:

- INTEGRATION_TEST_PATH=jobs/integration
- JUJU_DEPLOY_CHANNEL=beta

_Example_:

```
tox -e py36 -- ogc --spec validate/tigera-ee-spec.yml
```

### Validate CK with Vault

Run validation tests on CK with Vault enabled instead, replaces EasyRSA

_Jenkins Job_: validate-ck-vault

_Requires_:

Must have aws credentials setup and loaded within Juju credentials.

**Environment Variables**:

- INTEGRATION_TEST_PATH=jobs/integration
- JUJU_DEPLOY_CHANNEL=beta

_Example_:

```
tox -e py36 -- ogc --spec validate/vault-spec.yml
```

### Validate CK with Ceph

Run validation tests on CK with Ceph enabled

_Jenkins Job_: validate-ck-ceph

_Requires_:

Must have aws credentials setup and loaded within Juju credentials.

**Environment Variables**:

- INTEGRATION_TEST_PATH=jobs/integration
- JUJU_DEPLOY_CHANNEL=beta

_Example_:

```
tox -e py36 -- ogc --spec validate/ceph-spec.yml
```

### Validate CK with NVidia

Run validation tests on CK with NVidia enabled instead

_Jenkins Job_: validate-ck-nvidia

_Requires_:

Must have aws credentials setup and loaded within Juju credentials.

**Environment Variables**:

- INTEGRATION_TEST_PATH=jobs/integration
- JUJU_DEPLOY_CHANNEL=beta

_Example_:

```
tox -e py36 -- ogc --spec validate/nvidia-spec.yml
```

### Validate CK with AWS IAM

Run validation tests on CK with AWS IAM enabled

_Jenkins Job_: validate-ck-aws-iam

_Requires_:

Must have aws credentials setup and loaded within Juju credentials.

**Environment Variables**:

- INTEGRATION_TEST_PATH=jobs/integration
- JUJU_DEPLOY_CHANNEL=beta

_Example_:

```
tox -e py36 -- ogc --spec validate/aws-iam-spec.yml
```

### CNCF Conformance (TBW)

### Notify Solutions QA

Notify solutions-qa that CK is ready to be run through their tests. Once
that is complete and relayed to us, we can start the release to stable.

### Document release notes

- Bugfixes
- Enhancements
- Known Limitations/Issues

### Promote charms from **beta** to **stable**

This job takes a tag, from_channel, and to_channel. The tag defaults to `k8s` so
it will only promote the necessary charms that make up charmed-kuberneetes (the
others are kubeflow related).

_Jenkins Job_: promote-charms

_Requirements_:

**Environment Variables**:

- TOX_WORK_DIR=~/.tox
- FROM_CHANNEL=beta
- TO_CHANNEL=stable
- CHARM_LIST=jobs/includes/charm-support-matrix.inc
- FILTER_BY_TAG=k8s


_Example_:

```
tox -e py36 -- ogc jobs/build-charms/spec.yml -t promote-charms
```

### Promote bundles from **beta** to **stable**

Same as charm promotion.

_Jenkins Job_: promote-bundles

_Requirements_:

**Environment Variables**:

- TOX_WORK_DIR=~/.tox
- FROM_CHANNEL=beta
- TO_CHANNEL=stable
- CHARM_LIST=jobs/includes/charm-support-matrix.inc
- FILTER_BY_TAG=k8s


_Example_:

```
tox -e py36 -- ogc jobs/build-charms/spec.yml -t promote-bundles
```

### Send announcement

Email annoucement to k8s-crew with any relevant information.

