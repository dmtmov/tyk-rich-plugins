# tyk-plugin-system

# Contribute

Before we start, let's understand how deployment works.
There are two workflows in Github Actions.

*build-pr.yaml* pushes a bundle with the commit id in filename.
*push-dev.yaml* waits from you two manual inputs:
- name of plugin you want to deploy
- version of this plugin
The workflow takes params and push teh bundle to Dev environment.

If you want to add a new plugin, you should follow two steps:
- TBD
