# Pruple Help and Documentation

### Creating a New Pruple Cluster

A **Pruple cluster** is a managed collection of repositories under Pruple's control.
Follow these steps to create one:

---

#### 1. Create a GitHub Organization *(optional but recommended)*

While you can host a Pruple cluster directly under your user account, using an **organization** is safer and more flexible.

It helps you:

* Avoid overwriting personal projects
* Reuse the same repository names across different clusters
* Collaborate more easily with other users

> You can skip this step if you prefer, but using an organization is strongly advised.

---

#### 2. Fork the `pruple_core` Repository

Fork the [`pruple_core`](https://github.com/pruplestack/pruple_core) repository into your organization (or user space).
This fork will act as the **central controller** for your cluster.

---

#### 3. Create a GitHub Access Token

You’ll need a token so the CI pipeline can create and update repositories automatically.

Choose **one** of the following options:

* **Classic personal access token** with `repo` and `gist` scopes
* **Fine-grained personal access token** with only the required permissions (to be documented later)

Keep this token private as it grants access to your GitHub account and can be abused if leaked.

---

#### 4. Add the Token as a Repository Secret

In your fork of `pruple_core`, go to **Settings → Secrets and variables → Actions → New repository secret**.
Create a secret named **`PRUPLE_KEY_TO_THOUGHTS`** and paste the token value.

As long as it stays within repository secrets, it is safe unless you modify the workflows to expose it.

---

#### 5. Create the Tag Map Configuration

In your forked `pruple_core`, create or update a file at:

```
/ci/tag_maps.yaml
```

Example structure:

```yaml
repos:
  repo1:
    url: "pruplestack/repo1"
  repo2:
    url: "pruplestack/repo2"
  repo3:
    url: "pruplestack/repo3"
  repo4:
    url: "pruplestack/repo4"
  repo5:
    url: "pruplestack/repo5"

tag_map:
  - repo1: ["tag1", "tag2"]
  - repo2: ["tag3", "tag4"]
  - repo3: ["tag5", "tag6"]
  - repo4: ["tag1", "tag3"]
  - repo5: ["tag2", "tag4"]
```

Replace:

* `pruplestack` with your organization (or user) name [^1]
* `repo1`, `repo2`, etc. with your actual repository names
* `tag1`, `tag2`, etc. with the tags that should route files to each repository

> Repositories listed here will be created automatically the first time a tagged file is dispatched to them.
> If the repo already exists, it will be used as-is if it has "managed by pruple" in the description.
> make sure to add that description to any pre-existing repositories you want to use. and not to any others.
> Ensure the names are unique within your GitHub account or organization.
> Tags can be any string but should be consistent with the tags used in the files you plan to push.
> don't add pruple_core to the tag map as it is used only as the controller and would create a recursive loop. that will use up your github actions minutes and
> may hit rate limits.
> dont create more than 1000 repositories

[^1]: If you change the organization/user name later, remember to update this configuration accordingly.also if you put in a different organization/user name than your pruple_core fork is in, the token you created will try to create repos in that other organization/user and will likely fail unless you have access there.
---

#### 6. Push and Dispatch

Once configured, any file pushed to your `pruple_core` fork will trigger the CI workflow.
The workflow reads your `tag_maps.yaml` and **dispatches each file** to the appropriate repositories based on the tags defined.

