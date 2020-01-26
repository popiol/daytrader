# lifecycle

## Functions

1. Create new project template with lifecycle repo as submodule
1. Create new dev brach from master
1. Deploy dev branch to AWS
1. Commit & push dev branch once a day
1. Automated tests of dev deployment
1. Merge from dev to release
1. Merge from master to release
1. Deploy release branch to AWS
1. Automated tests of release deployment
1. Merge from release to master
1. Deploy master branch to AWS
1. Automated tests of prod deployment
1. Commit & push master branch once a day
