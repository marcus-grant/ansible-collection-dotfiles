# Ansible Collection - marcus_grant.dotfiles

My colleciton of Ansible roles and modules that are used to setup myself as a developer or admin for basically all of my systems, be they servers, workstations, containers, or even embedded devices. I'm going to attempt to make these roles as general use as possible, so feel free to use them through ansible galaxy, fork them, or use them as a template for your own collection/roles. If you see a problem with any of them you'd like me to address please file an issue and/or provide pull requests and I'll get to them.

## Roles

* Bash
  * A role that installs, sets as default shell, git clones a dotfiles repo, and symlinks all expected file locations to their respective locations in the dotfile repo.
  * [Role link](https://github.com/marcus-grant/ansible-collection-dotfiles/tree/main/roles/bash)
