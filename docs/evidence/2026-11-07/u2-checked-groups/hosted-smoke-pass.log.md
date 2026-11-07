````text
﻿2026-11-07T07:07:54.9960194Z Current runner version: '2.338.2'
2026-11-07T07:07:54.9978380Z ##[group]Runner Image Provisioner
2026-11-07T07:07:54.9978941Z Hosted Compute Agent
2026-11-07T07:07:54.9979345Z Version: 20261028.624
2026-11-07T07:07:54.9979765Z Commit: 54898b74c23fde5556c9b3c3a2290865feef0dfe
2026-11-07T07:07:54.9980174Z Build Date: 2026-10-28T21:51:42Z
2026-11-07T07:07:54.9980625Z Worker ID: {9a380f71-2b63-4c74-a647-9f0febfab7ad}
2026-11-07T07:07:54.9981065Z Region: westus3
2026-11-07T07:07:54.9981420Z Cloud: Azure
2026-11-07T07:07:54.9981757Z ##[endgroup]
2026-11-07T07:07:54.9982475Z ##[group]Operating System
2026-11-07T07:07:54.9982869Z Ubuntu
2026-11-07T07:07:54.9983272Z 24.04.5
2026-11-07T07:07:54.9983571Z LTS
2026-11-07T07:07:54.9983953Z ##[endgroup]
2026-11-07T07:07:54.9984283Z ##[group]Runner Image
2026-11-07T07:07:54.9984668Z Image: ubuntu-24.04
2026-11-07T07:07:54.9985043Z Version: 20261101.360.1
2026-11-07T07:07:54.9986303Z Included Software: https://github.com/actions/runner-images/blob/ubuntu24/20261101.360/images/ubuntu/Ubuntu2404-Readme.md
2026-11-07T07:07:54.9987160Z Image Release: https://github.com/actions/runner-images/releases/tag/ubuntu24%2F20261101.360
2026-11-07T07:07:54.9987742Z ##[endgroup]
2026-11-07T07:07:54.9988432Z ##[group]GITHUB_TOKEN Permissions
2026-11-07T07:07:54.9989653Z Contents: read
2026-11-07T07:07:54.9989998Z Metadata: read
2026-11-07T07:07:54.9990326Z ##[endgroup]
2026-11-07T07:07:54.9991914Z Secret source: Actions
2026-11-07T07:07:54.9992458Z Cache mode: write
2026-11-07T07:07:54.9993038Z Prepare workflow directory
2026-11-07T07:07:55.0225744Z Prepare all required actions
2026-11-07T07:07:55.0255533Z Getting action download info
2026-11-07T07:07:55.3259867Z Download action repository 'actions/checkout@v6' (SHA:d23441a48e516b6c34aea4fa41551a30e30af803)
2026-11-07T07:07:55.4123520Z Download action repository 'actions/setup-python@v6' (SHA:ece7cb06caefa5fff74198d8649806c4678c61a1)
2026-11-07T07:07:55.5074381Z Download action repository 'actions/upload-artifact@v6' (SHA:b7c566a772e6b6bfb58ed0dc250532a479d7789f)
2026-11-07T07:07:55.7312070Z Complete job name: Focused Linux smoke
2026-11-07T07:07:55.7784426Z ##[group]Run actions/checkout@v6
2026-11-07T07:07:55.7784809Z with:
2026-11-07T07:07:55.7785040Z   repository: eristavi/eristavi-lang
2026-11-07T07:07:55.7787202Z   token: ***
2026-11-07T07:07:55.7787424Z   ssh-strict: true
2026-11-07T07:07:55.7787657Z   ssh-user: git
2026-11-07T07:07:55.7787895Z   persist-credentials: true
2026-11-07T07:07:55.7788147Z   clean: true
2026-11-07T07:07:55.7788384Z   sparse-checkout-cone-mode: true
2026-11-07T07:07:55.7788654Z   fetch-depth: 1
2026-11-07T07:07:55.7788878Z   fetch-tags: false
2026-11-07T07:07:55.7789108Z   show-progress: true
2026-11-07T07:07:55.7789339Z   lfs: false
2026-11-07T07:07:55.7789555Z   submodules: false
2026-11-07T07:07:55.7789791Z   set-safe-directory: true
2026-11-07T07:07:55.7790057Z   allow-unsafe-pr-checkout: false
2026-11-07T07:07:55.7790389Z env:
2026-11-07T07:07:55.7790591Z   CC: clang
2026-11-07T07:07:55.7790808Z   CFLAGS: -O2
2026-11-07T07:07:55.7791040Z ##[endgroup]
2026-11-07T07:07:55.9934414Z Syncing repository: eristavi/eristavi-lang
2026-11-07T07:07:55.9936059Z ##[group]Getting Git version info
2026-11-07T07:07:55.9936576Z Working directory is '/home/runner/work/eristavi-lang/eristavi-lang'
2026-11-07T07:07:55.9937200Z [command]/usr/bin/git version
2026-11-07T07:07:56.0020733Z git version 2.56.0
2026-11-07T07:07:56.0033651Z ##[endgroup]
2026-11-07T07:07:56.0049193Z Temporarily overriding HOME='/home/runner/work/_temp/3bd3744c-3af9-4dc1-bf5e-ac5cdb6e7706' before making global git config changes
2026-11-07T07:07:56.0051987Z Adding repository directory to the temporary git global config as a safe directory
2026-11-07T07:07:56.0053079Z [command]/usr/bin/git config --global --add safe.directory /home/runner/work/eristavi-lang/eristavi-lang
2026-11-07T07:07:56.0099647Z Deleting the contents of '/home/runner/work/eristavi-lang/eristavi-lang'
2026-11-07T07:07:56.0103097Z ##[group]Determining repository object format
2026-11-07T07:07:56.0104504Z ##[endgroup]
2026-11-07T07:07:56.0105287Z ##[group]Initializing the repository
2026-11-07T07:07:56.0107272Z [command]/usr/bin/git init /home/runner/work/eristavi-lang/eristavi-lang
2026-11-07T07:07:56.0203853Z hint: Using 'master' as the name for the initial branch. This default branch name
2026-11-07T07:07:56.0204809Z hint: will change to "main" in Git 3.0. To configure the initial branch name
2026-11-07T07:07:56.0205786Z hint: to use in all of your new repositories, which will suppress this warning,
2026-11-07T07:07:56.0206487Z hint: call:
2026-11-07T07:07:56.0206847Z hint:
2026-11-07T07:07:56.0207318Z hint: 	git config --global init.defaultBranch <name>
2026-11-07T07:07:56.0207882Z hint:
2026-11-07T07:07:56.0208519Z hint: Names commonly chosen instead of 'master' are 'main', 'trunk' and
2026-11-07T07:07:56.0209384Z hint: 'development'. The just-created branch can be renamed via this command:
2026-11-07T07:07:56.0210072Z hint:
2026-11-07T07:07:56.0210439Z hint: 	git branch -m <name>
2026-11-07T07:07:56.0210889Z hint:
2026-11-07T07:07:56.0211485Z hint: Disable this message with "git config set advice.defaultBranchName false"
2026-11-07T07:07:56.0216936Z Initialized empty Git repository in /home/runner/work/eristavi-lang/eristavi-lang/.git/
2026-11-07T07:07:56.0224849Z [command]/usr/bin/git remote add origin https://github.com/eristavi/eristavi-lang
2026-11-07T07:07:56.0266199Z ##[endgroup]
2026-11-07T07:07:56.0267261Z ##[group]Disabling automatic garbage collection
2026-11-07T07:07:56.0268535Z [command]/usr/bin/git config --local gc.auto 0
2026-11-07T07:07:56.0296329Z ##[endgroup]
2026-11-07T07:07:56.0297571Z ##[group]Setting up auth
2026-11-07T07:07:56.0298088Z Removing SSH command configuration
2026-11-07T07:07:56.0301066Z [command]/usr/bin/git config --local --name-only --get-regexp core\.sshCommand
2026-11-07T07:07:56.0330380Z [command]/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'core\.sshCommand' && git config --local --unset-all 'core.sshCommand' || :"
2026-11-07T07:07:56.0644726Z Removing HTTP extra header
2026-11-07T07:07:56.0650301Z [command]/usr/bin/git config --local --name-only --get-regexp http\.https\:\/\/github\.com\/\.extraheader
2026-11-07T07:07:56.0697653Z [command]/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'http\.https\:\/\/github\.com\/\.extraheader' && git config --local --unset-all 'http.https://github.com/.extraheader' || :"
2026-11-07T07:07:56.0891679Z Removing includeIf entries pointing to credentials config files
2026-11-07T07:07:56.0897090Z [command]/usr/bin/git config --local --name-only --get-regexp ^includeIf\.gitdir:
2026-11-07T07:07:56.0930728Z [command]/usr/bin/git submodule foreach --recursive git config --local --show-origin --name-only --get-regexp remote.origin.url
2026-11-07T07:07:56.1110891Z [command]/usr/bin/git config --file /home/runner/work/_temp/git-credentials-579fd627-0dbc-4629-990f-24eb2c95d6ac.config http.https://github.com/.extraheader AUTHORIZATION: basic ***
2026-11-07T07:07:56.1147614Z [command]/usr/bin/git config --local includeIf.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git.path /home/runner/work/_temp/git-credentials-579fd627-0dbc-4629-990f-24eb2c95d6ac.config
2026-11-07T07:07:56.1180636Z [command]/usr/bin/git config --local includeIf.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git/worktrees/*.path /home/runner/work/_temp/git-credentials-579fd627-0dbc-4629-990f-24eb2c95d6ac.config
2026-11-07T07:07:56.1213832Z [command]/usr/bin/git config --local includeIf.gitdir:/github/workspace/.git.path /github/runner_temp/git-credentials-579fd627-0dbc-4629-990f-24eb2c95d6ac.config
2026-11-07T07:07:56.1251760Z [command]/usr/bin/git config --local includeIf.gitdir:/github/workspace/.git/worktrees/*.path /github/runner_temp/git-credentials-579fd627-0dbc-4629-990f-24eb2c95d6ac.config
2026-11-07T07:07:56.1282436Z ##[endgroup]
2026-11-07T07:07:56.1282865Z ##[group]Fetching the repository
2026-11-07T07:07:56.1288133Z [command]/usr/bin/git -c protocol.version=2 fetch --no-tags --prune --no-recurse-submodules --depth=1 origin +43d56f2f526fd57db5d790413217de439858b7a5:refs/remotes/origin/compiler/u2-cleanup-foundation-20261102
2026-11-07T07:07:57.1114330Z From https://github.com/eristavi/eristavi-lang
2026-11-07T07:07:57.1115916Z  * [new ref]         43d56f2f526fd57db5d790413217de439858b7a5 -> origin/compiler/u2-cleanup-foundation-20261102
2026-11-07T07:07:57.1122783Z [command]/usr/bin/git branch --list --remote origin/compiler/u2-cleanup-foundation-20261102
2026-11-07T07:07:57.1151962Z   origin/compiler/u2-cleanup-foundation-20261102
2026-11-07T07:07:57.1158454Z [command]/usr/bin/git rev-parse refs/remotes/origin/compiler/u2-cleanup-foundation-20261102
2026-11-07T07:07:57.1185414Z 43d56f2f526fd57db5d790413217de439858b7a5
2026-11-07T07:07:57.1189957Z ##[endgroup]
2026-11-07T07:07:57.1191241Z ##[group]Determining the checkout info
2026-11-07T07:07:57.1192630Z ##[endgroup]
2026-11-07T07:07:57.1193502Z [command]/usr/bin/git sparse-checkout disable
2026-11-07T07:07:57.1254632Z [command]/usr/bin/git config --local --unset-all extensions.worktreeConfig
2026-11-07T07:07:57.1287447Z ##[group]Checking out the ref
2026-11-07T07:07:57.1289739Z [command]/usr/bin/git checkout --progress --force -B compiler/u2-cleanup-foundation-20261102 refs/remotes/origin/compiler/u2-cleanup-foundation-20261102
2026-11-07T07:07:57.1884325Z Switched to a new branch 'compiler/u2-cleanup-foundation-20261102'
2026-11-07T07:07:57.1889022Z branch 'compiler/u2-cleanup-foundation-20261102' set up to track 'origin/compiler/u2-cleanup-foundation-20261102'.
2026-11-07T07:07:57.1895601Z ##[endgroup]
2026-11-07T07:07:57.1936392Z [command]/usr/bin/git log -1 --format=%H
2026-11-07T07:07:57.1963819Z 43d56f2f526fd57db5d790413217de439858b7a5
2026-11-07T07:07:57.2277540Z ##[group]Run actions/setup-python@v6
2026-11-07T07:07:57.2278183Z with:
2026-11-07T07:07:57.2278694Z   python-version: 3.11
2026-11-07T07:07:57.2279243Z   check-latest: false
2026-11-07T07:07:57.2284039Z   token: ***
2026-11-07T07:07:57.2284563Z   update-environment: true
2026-11-07T07:07:57.2285302Z   allow-prereleases: false
2026-11-07T07:07:57.2285891Z   freethreaded: false
2026-11-07T07:07:57.2286406Z env:
2026-11-07T07:07:57.2286859Z   CC: clang
2026-11-07T07:07:57.2287337Z   CFLAGS: -O2
2026-11-07T07:07:57.2287835Z ##[endgroup]
2026-11-07T07:07:57.3140230Z ##[group]Installed versions
2026-11-07T07:07:57.3203072Z Successfully set up CPython (3.11.18)
2026-11-07T07:07:57.3204231Z ##[endgroup]
2026-11-07T07:07:57.3343761Z ##[group]Run python -m pip install -e .
2026-11-07T07:07:57.3344505Z [36;1mpython -m pip install -e .[0m
2026-11-07T07:07:57.3380893Z shell: /usr/bin/bash -e {0}
2026-11-07T07:07:57.3381812Z env:
2026-11-07T07:07:57.3382500Z   CC: clang
2026-11-07T07:07:57.3383193Z   CFLAGS: -O2
2026-11-07T07:07:57.3384100Z   pythonLocation: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:07:57.3385607Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib/pkgconfig
2026-11-07T07:07:57.3386974Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:07:57.3388249Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:07:57.3389512Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:07:57.3390780Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib
2026-11-07T07:07:57.3391856Z ##[endgroup]
2026-11-07T07:07:57.9331343Z Obtaining file:///home/runner/work/eristavi-lang/eristavi-lang
2026-11-07T07:07:57.9340215Z   Installing build dependencies: started
2026-11-07T07:07:58.4331350Z   Installing build dependencies: finished with status 'done'
2026-11-07T07:07:58.4335830Z   Checking if build backend supports build_editable: started
2026-11-07T07:07:58.6357268Z   Checking if build backend supports build_editable: finished with status 'done'
2026-11-07T07:07:58.6362545Z   Getting requirements to build editable: started
2026-11-07T07:07:58.8246631Z   Getting requirements to build editable: finished with status 'done'
2026-11-07T07:07:58.8253027Z   Preparing editable metadata (pyproject.toml): started
2026-11-07T07:07:58.9275528Z   Preparing editable metadata (pyproject.toml): finished with status 'done'
2026-11-07T07:07:59.2480371Z Collecting regex==2026.9.29 (from eristavi-lang==0.0.1.dev0)
2026-11-07T07:07:59.2994469Z   Downloading regex-2026.9.29-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (40 kB)
2026-11-07T07:07:59.3418595Z Collecting unicodedata2==17.0.0 (from eristavi-lang==0.0.1.dev0)
2026-11-07T07:07:59.3521199Z   Downloading unicodedata2-17.0.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (3.3 kB)
2026-11-07T07:07:59.3641946Z Downloading regex-2026.9.29-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (804 kB)
2026-11-07T07:07:59.3950504Z    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 805.0/805.0 kB 43.8 MB/s  0:00:00
2026-11-07T07:07:59.4052466Z Downloading unicodedata2-17.0.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (531 kB)
2026-11-07T07:07:59.4099279Z    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 531.5/531.5 kB 97.7 MB/s  0:00:00
2026-11-07T07:07:59.4149658Z Building wheels for collected packages: eristavi-lang
2026-11-07T07:07:59.4154864Z   Building editable for eristavi-lang (pyproject.toml): started
2026-11-07T07:07:59.5347988Z   Building editable for eristavi-lang (pyproject.toml): finished with status 'done'
2026-11-07T07:07:59.5351860Z   Created wheel for eristavi-lang: filename=eristavi_lang-0.0.1.dev0-0.editable-py3-none-any.whl size=4073 sha256=f2303e65546dae123aeb14bdf704b63eee08a01e178473f100867d335ce90806
2026-11-07T07:07:59.5352663Z   Stored in directory: /tmp/pip-ephem-wheel-cache-xnr8g0c8/wheels/bf/0e/13/3c92c3d16e7da71040fe0218774d6a7875df473d79c0e7b5aa
2026-11-07T07:07:59.5363466Z Successfully built eristavi-lang
2026-11-07T07:07:59.5463207Z Installing collected packages: unicodedata2, regex, eristavi-lang
2026-11-07T07:07:59.6368202Z
2026-11-07T07:07:59.6373253Z Successfully installed eristavi-lang-0.0.1.dev0 regex-2026.9.29 unicodedata2-17.0.0
2026-11-07T07:07:59.6378165Z
2026-11-07T07:07:59.6378332Z [notice] A new release of pip is available: 26.2.2 -> 26.3
2026-11-07T07:07:59.6378646Z [notice] To update, run: pip install --upgrade pip
2026-11-07T07:07:59.6911792Z ##[group]Run python -m compileall -q compiler tests tools
2026-11-07T07:07:59.6912069Z [36;1mpython -m compileall -q compiler tests tools[0m
2026-11-07T07:07:59.6928884Z shell: /usr/bin/bash -e {0}
2026-11-07T07:07:59.6929016Z env:
2026-11-07T07:07:59.6929116Z   CC: clang
2026-11-07T07:07:59.6929218Z   CFLAGS: -O2
2026-11-07T07:07:59.6929366Z   pythonLocation: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:07:59.6929596Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib/pkgconfig
2026-11-07T07:07:59.6929817Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:07:59.6930017Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:07:59.6930219Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:07:59.6930436Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib
2026-11-07T07:07:59.6930607Z ##[endgroup]
2026-11-07T07:07:59.9107603Z ##[group]Run set -o pipefail
2026-11-07T07:07:59.9107775Z [36;1mset -o pipefail[0m
2026-11-07T07:07:59.9108110Z [36;1mpython -u tools/run_ci_tests.py --profile smoke --report "$RUNNER_TEMP/test-results.json" 2>&1 | tee "$RUNNER_TEMP/test-results.log"[0m
2026-11-07T07:07:59.9123495Z shell: /usr/bin/bash -e {0}
2026-11-07T07:07:59.9123624Z env:
2026-11-07T07:07:59.9123724Z   CC: clang
2026-11-07T07:07:59.9123825Z   CFLAGS: -O2
2026-11-07T07:07:59.9123969Z   pythonLocation: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:07:59.9124196Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib/pkgconfig
2026-11-07T07:07:59.9124439Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:07:59.9124639Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:07:59.9124840Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:07:59.9125303Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib
2026-11-07T07:07:59.9125488Z ##[endgroup]
2026-11-07T07:08:02.9400432Z test_actual_planner_matches_independent_unwind_and_refusal_oracles (test_u2_cleanup_plan.U2CleanupPlanTests.test_actual_planner_matches_independent_unwind_and_refusal_oracles) ... ok
2026-11-07T07:08:03.5524485Z test_independent_verifier_rejects_mutated_frozen_and_unreachable_plans (test_u2_cleanup_verify.U2CleanupVerifierTests.test_independent_verifier_rejects_mutated_frozen_and_unreachable_plans) ... ok
2026-11-07T07:08:04.6069841Z test_cleanup_links_require_matching_typed_destinations_and_origins (test_u2_continuation_bind.U2ContinuationBindingTests.test_cleanup_links_require_matching_typed_destinations_and_origins) ... ok
2026-11-07T07:08:05.5834739Z test_typed_destinations_and_same_revision_negative_matrix (test_u2_continuation_bind.U2ContinuationBindingTests.test_typed_destinations_and_same_revision_negative_matrix) ... ok
2026-11-07T07:08:07.4848825Z test_canonical_invoke_and_outcome_only_payload_availability (test_u2_invoke.U2InvokeTests.test_canonical_invoke_and_outcome_only_payload_availability) ... ok
2026-11-07T07:08:07.4849844Z test_owned_native_reference_outcomes_and_ingress (test_u2_invoke.U2InvokeTests.test_owned_native_reference_outcomes_and_ingress) ... skipped 'opt-in Linux x86-64 owned-runtime invoke reference probe'
2026-11-07T07:08:08.7077801Z test_partial_invoke_construction_cannot_publish_and_closes_backing (test_u2_invoke.U2InvokeTests.test_partial_invoke_construction_cannot_publish_and_closes_backing) ... ok
2026-11-07T07:08:10.8378437Z test_reference_execution_selects_typed_outcome_and_preserves_fuel (test_u2_invoke.U2InvokeTests.test_reference_execution_selects_typed_outcome_and_preserves_fuel) ... ok
2026-11-07T07:08:12.7544151Z test_zero_normal_results_have_no_fake_ssa_value (test_u2_invoke.U2InvokeTests.test_zero_normal_results_have_no_fake_ssa_value) ... ok
2026-11-07T07:08:14.9006791Z test_multiple_targets_unused_contract_mutations_and_exact_cleanup (test_u2_fallible_registry.U2FallibleRegistryTests.test_multiple_targets_unused_contract_mutations_and_exact_cleanup) ... ok
2026-11-07T07:08:14.9007548Z test_owned_runtime_preserves_outcome_transfers (test_u2_invoke_transfers.U2InvokeTransferTests.test_owned_runtime_preserves_outcome_transfers) ... skipped 'opt-in Linux x86-64 owned-runtime transfer probe'
2026-11-07T07:08:16.8647261Z test_predecessor_values_follow_each_typed_outcome_with_dominance (test_u2_invoke_transfers.U2InvokeTransferTests.test_predecessor_values_follow_each_typed_outcome_with_dominance) ... ok
2026-11-07T07:08:19.0269906Z test_reference_executes_carried_values_on_success_and_failure (test_u2_invoke_transfers.U2InvokeTransferTests.test_reference_executes_carried_values_on_success_and_failure) ... ok
2026-11-07T07:08:21.4884437Z test_inner_checked_close_failure_still_consumes_outer_owner (test_u2_scoped_owners.U2ScopedOwnerTests.test_inner_checked_close_failure_still_consumes_outer_owner) ... ok
2026-11-07T07:08:23.7910060Z test_live_owner_loop_signature_and_dead_block_rejection (test_u2_scoped_owners.U2ScopedOwnerTests.test_live_owner_loop_signature_and_dead_block_rejection) ... ok
2026-11-07T07:08:26.1291576Z test_nested_acquire_failure_close_consumption_and_origin (test_u2_scoped_owners.U2ScopedOwnerTests.test_nested_acquire_failure_close_consumption_and_origin) ... ok
2026-11-07T07:08:28.3693136Z test_ordinary_resource_construction_is_rejected (test_u2_scoped_owners.U2ScopedOwnerTests.test_ordinary_resource_construction_is_rejected) ... ok
2026-11-07T07:08:28.3694375Z test_owned_runtime_scoped_owner_proof_and_refusals (test_u2_scoped_owners.U2ScopedOwnerTests.test_owned_runtime_scoped_owner_proof_and_refusals) ... skipped 'opt-in Linux x86-64 owned scoped-owner proof'
2026-11-07T07:08:30.6048992Z test_resource_cannot_escape_through_an_ordinary_call (test_u2_scoped_owners.U2ScopedOwnerTests.test_resource_cannot_escape_through_an_ordinary_call) ... ok
2026-11-07T07:08:32.8196957Z test_return_cannot_bypass_cleanup (test_u2_scoped_owners.U2ScopedOwnerTests.test_return_cannot_bypass_cleanup) ... ok
2026-11-07T07:08:35.2475048Z test_two_stage_canonical_cleanup_uses_original_verified_plan (test_u2_scoped_owners.U2ScopedOwnerTests.test_two_stage_canonical_cleanup_uses_original_verified_plan) ... ok
2026-11-07T07:08:37.6998018Z test_verified_cleanup_plan_emits_canonical_close_on_both_exit_modes (test_u2_scoped_owners.U2ScopedOwnerTests.test_verified_cleanup_plan_emits_canonical_close_on_both_exit_modes) ... ok
2026-11-07T07:08:37.9728794Z test_primary_and_ordered_typed_context (test_u2_typed_failure_context.U2TypedFailureContextTests.test_primary_and_ordered_typed_context) ... ok
2026-11-07T07:08:38.2797775Z test_primary_and_ordered_cleanup_failures (test_u2_failure_order.U2FailureOrderTests.test_primary_and_ordered_cleanup_failures) ... ok
2026-11-07T07:08:38.8844528Z test_three_owner_primary_and_ordered_secondary_matrix (test_u2_failure_trace.U2FailureTraceTests.test_three_owner_primary_and_ordered_secondary_matrix) ... ok
2026-11-07T07:08:41.1551203Z test_checked_failure_payload_pins_full_typed_context (test_u2_failure_root_binding.U2FailureRootBindingTests.test_checked_failure_payload_pins_full_typed_context) ... ok
2026-11-07T07:08:51.4366680Z test_owned_failure_root_reference_survives_allocation_pressure (test_u2_failure_root_binding.U2FailureRootBindingTests.test_owned_failure_root_reference_survives_allocation_pressure) ... ok
2026-11-07T07:08:53.7537808Z test_all_canonical_invoke_failure_roots_and_refusals (test_u2_root_map.U2RootMapTests.test_all_canonical_invoke_failure_roots_and_refusals) ... ok
2026-11-07T07:08:56.3480717Z test_checked_cleanup_ssa_liveness_and_adversarial_mutations (test_u2_ssa_liveness.U2SSALivenessTests.test_checked_cleanup_ssa_liveness_and_adversarial_mutations) ... ok
2026-11-07T07:08:58.6140538Z test_backedge_parallel_phi_and_safe_point_liveness (test_u2_ssa_loops.U2SSALoopsTests.test_backedge_parallel_phi_and_safe_point_liveness) ... ok
2026-11-07T07:09:01.1820854Z test_recursive_managed_value_live_at_call_safepoint (test_u2_ssa_recursion.U2SSARecursionTests.test_recursive_managed_value_live_at_call_safepoint) ... ok
2026-11-07T07:09:01.9127906Z test_versioned_text_list_identity_descriptors_and_corruption (test_u2_managed_types.U2ManagedTypesTests.test_versioned_text_list_identity_descriptors_and_corruption) ... ok
2026-11-07T07:09:04.3087052Z test_verified_identity_descriptor_and_cfg_safe_point_refusals (test_u2_identity_root_gate.U2IdentityRootGateTests.test_verified_identity_descriptor_and_cfg_safe_point_refusals) ... ok
2026-11-07T07:09:11.9125028Z test_invalid_identity_descriptor_rejected_without_assembly (test_u2_identity_native_publication.U2IdentityNativePublicationTests.test_invalid_identity_descriptor_rejected_without_assembly) ... ok
2026-11-07T07:09:14.5163123Z test_mismatched_mixed_managed_descriptor_refuses_before_emission (test_u2_identity_native_publication.U2IdentityNativePublicationTests.test_mismatched_mixed_managed_descriptor_refuses_before_emission) ... ok
2026-11-07T07:09:17.1207421Z test_mixed_text_list_identity_root_publication (test_u2_identity_native_publication.U2IdentityNativePublicationTests.test_mixed_text_list_identity_root_publication) ... ok
2026-11-07T07:09:19.6007035Z test_more_than_32_selected_identity_roots_emit_exact_offsets (test_u2_identity_native_publication.U2IdentityNativePublicationTests.test_more_than_32_selected_identity_roots_emit_exact_offsets) ... ok
2026-11-07T07:09:22.5653854Z test_verified_identity_ssa_root_before_after_and_native_gc (test_u2_identity_native_publication.U2IdentityNativePublicationTests.test_verified_identity_ssa_root_before_after_and_native_gc) ... ok
2026-11-07T07:09:25.3693240Z test_canonical_identity_carries_and_wrong_source_refusals (test_u2_checked_identity_ssa.U2CheckedIdentitySSATests.test_canonical_identity_carries_and_wrong_source_refusals) ... ok
2026-11-07T07:09:28.1567381Z test_wrong_identity_descriptor_refused_before_checked_edge_admission (test_u2_checked_identity_ssa.U2CheckedIdentitySSATests.test_wrong_identity_descriptor_refused_before_checked_edge_admission) ... ok
2026-11-07T07:09:36.6704542Z test_emitted_checked_identity_edges_preserve_live_gc_roots (test_u2_checked_identity_edge.U2CheckedIdentityEdgeTests.test_emitted_checked_identity_edges_preserve_live_gc_roots) ... ok
2026-11-07T07:09:39.5500157Z test_wrong_managed_identity_refuses_before_assembly (test_u2_checked_identity_edge.U2CheckedIdentityEdgeTests.test_wrong_managed_identity_refuses_before_assembly) ... ok
2026-11-07T07:09:48.0619252Z test_real_file_close_publishes_identity_on_both_checked_edges (test_u2_checked_identity_close.U2CheckedIdentityCloseTests.test_real_file_close_publishes_identity_on_both_checked_edges) ... ok
2026-11-07T07:09:51.1799742Z test_wrong_identity_descriptor_rejected_before_native_emission (test_u2_checked_identity_close.U2CheckedIdentityCloseTests.test_wrong_identity_descriptor_rejected_before_native_emission) ... ok
2026-11-07T07:09:58.5662294Z test_entire_verified_function_loop_parallel_phi_and_dead_block (test_u2_function_scalar_native.U2FunctionScalarNativeTests.test_entire_verified_function_loop_parallel_phi_and_dead_block) ... ok
2026-11-07T07:10:00.8245298Z test_native_comparison_branch_matches_canonical_reference (test_u2_function_scalar_native.U2FunctionScalarNativeTests.test_native_comparison_branch_matches_canonical_reference) ... ok
2026-11-07T07:10:03.1909855Z test_native_signed_wrap_arithmetic (test_u2_function_scalar_native.U2FunctionScalarNativeTests.test_native_signed_wrap_arithmetic) ... ok
2026-11-07T07:10:05.4832127Z test_sparse_unsigned_switch_parallel_edges (test_u2_function_scalar_native.U2FunctionScalarNativeTests.test_sparse_unsigned_switch_parallel_edges) ... ok
2026-11-07T07:10:07.6523377Z test_unsupported_dead_aggregate_rejected_before_assembly (test_u2_function_scalar_native.U2FunctionScalarNativeTests.test_unsupported_dead_aggregate_rejected_before_assembly) ... ok
2026-11-07T07:10:15.9631714Z test_mixed_text_and_identity_roots_across_loop_and_return (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_mixed_text_and_identity_roots_across_loop_and_return) ... ok
2026-11-07T07:10:19.4425037Z test_recursive_function_parent_only_text_roots_and_scalar_result (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_recursive_function_parent_only_text_roots_and_scalar_result) ... ok
2026-11-07T07:10:35.3000360Z test_recursive_import_or_mismatched_signature_rejected_before_emission (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_recursive_import_or_mismatched_signature_rejected_before_emission) ... ok
2026-11-07T07:10:38.4800358Z test_recursive_two_managed_results_handoff_before_child_scope_leave (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_recursive_two_managed_results_handoff_before_child_scope_leave) ... ok
2026-11-07T07:10:41.7034857Z test_reject_managed_producer_in_dead_block_before_emission (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_reject_managed_producer_in_dead_block_before_emission) ... ok
2026-11-07T07:10:45.0779058Z test_reject_mismatched_identity_descriptor_before_emission (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_reject_mismatched_identity_descriptor_before_emission) ... ok
2026-11-07T07:10:48.2254084Z test_whole_function_identity_phi_and_gc_with_rooted_return (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_whole_function_identity_phi_and_gc_with_rooted_return) ... ok
2026-11-07T07:10:56.9531089Z test_checked_failure_handler_returns_normal_through_parent_frames (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_failure_handler_returns_normal_through_parent_frames) ... ok
2026-11-07T07:11:00.5495606Z test_checked_no_value_success_and_typed_failure_have_no_fake_result (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_no_value_success_and_typed_failure_have_no_fake_result) ... ok
2026-11-07T07:11:04.1236338Z test_checked_one_scalar_result_and_failure_use_distinct_outcomes (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_one_scalar_result_and_failure_use_distinct_outcomes) ... ok
2026-11-07T07:11:08.5180862Z test_checked_recursion_retains_complete_ordered_secondary_context (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_recursion_retains_complete_ordered_secondary_context) ... ok
2026-11-07T07:11:12.5782895Z test_checked_recursive_normal_failure_edges_roots_and_reclamation (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_recursive_normal_failure_edges_roots_and_reclamation) ... ok
2026-11-07T07:11:16.1323732Z test_checked_two_managed_normal_results_and_failed_result_are_disjoint (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_two_managed_normal_results_and_failed_result_are_disjoint) ... ok
2026-11-07T07:11:18.4549295Z test_failure_return_cannot_bypass_an_active_file_owner (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_failure_return_cannot_bypass_an_active_file_owner) ... ok
2026-11-07T07:11:49.2002048Z test_malformed_body_and_dead_failure_returns_refuse_before_emission (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_malformed_body_and_dead_failure_returns_refuse_before_emission) ... ok
2026-11-07T07:11:52.6707123Z test_missing_native_failure_handoff_or_payload_is_a_terminal_defect (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_missing_native_failure_handoff_or_payload_is_a_terminal_defect) ... ok
2026-11-07T07:13:19.4082420Z test_owned_and_c_bootstrap_generators_emit_identical_checked_function (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_owned_and_c_bootstrap_generators_emit_identical_checked_function) ... U2_CHECKED_OWNED_GENERATOR_SECONDS=78.36263252200001
2026-11-07T07:13:22.9165938Z ok
2026-11-07T07:13:26.4118906Z test_whole_publication_table_refuses_corruption_and_releases_on_refusal (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_whole_publication_table_refuses_corruption_and_releases_on_refusal) ... ok
2026-11-07T07:14:18.6674915Z test_closed_group_refusals_precede_all_assembly (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_closed_group_refusals_precede_all_assembly) ... ok
2026-11-07T07:14:22.1708537Z test_different_member_recovers_failure_into_normal_parent_result (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_different_member_recovers_failure_into_normal_parent_result) ... ok
2026-11-07T07:14:25.8256719Z test_distinct_normal_signatures_and_result_positions (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_distinct_normal_signatures_and_result_positions) ... ok
2026-11-07T07:14:29.2441682Z test_list_value_crosses_mutual_frames_and_preserves_snapshot (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_list_value_crosses_mutual_frames_and_preserves_snapshot) ... ok
2026-11-07T07:14:32.7967999Z test_missing_sibling_handoff_roots_are_terminal_defects (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_missing_sibling_handoff_roots_are_terminal_defects) ... ok
2026-11-07T07:14:36.7838139Z test_mutual_checked_frames_gc_and_independent_source_outcomes (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_mutual_checked_frames_gc_and_independent_source_outcomes) ... ok
2026-11-07T07:14:41.1831747Z test_mutual_frames_preserve_primary_and_ordered_secondary_context (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_mutual_frames_preserve_primary_and_ordered_secondary_context) ... ok
2026-11-07T07:14:44.8179043Z test_mutual_native_frame_stack_bound_and_reclamation (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_mutual_native_frame_stack_bound_and_reclamation) ... U2_MUTUAL_STACK=[{"depth": 0, "function_stack_bytes": 592}, {"depth": 1, "function_stack_bytes": 1184}, {"depth": 5, "function_stack_bytes": 3552}, {"depth": 32, "function_stack_bytes": 19536}, {"depth": 64, "function_stack_bytes": 38480}]
2026-11-07T07:14:44.8179991Z ok
2026-11-07T07:16:10.7735904Z test_owned_and_c_generators_agree_on_direct_group (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_owned_and_c_generators_agree_on_direct_group) ... U2_DIRECT_GROUP_OWNED_GENERATOR_SECONDS=74.805
2026-11-07T07:16:10.8586041Z ok
2026-11-07T07:16:17.7672794Z test_preflight_work_and_capacity_refusal_release_owned_plans (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_preflight_work_and_capacity_refusal_release_owned_plans) ... ok
2026-11-07T07:16:21.3838187Z test_two_managed_results_cross_member_handoff (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_two_managed_results_cross_member_handoff) ... ok
2026-11-07T07:16:29.7988345Z test_existing_list_copy_import_inside_original_loop (test_u2_function_import_integration.U2FunctionImportIntegrationTests.test_existing_list_copy_import_inside_original_loop) ... ok
2026-11-07T07:16:33.0454672Z test_existing_list_snapshot_append_count_gc_in_whole_function (test_u2_function_import_integration.U2FunctionImportIntegrationTests.test_existing_list_snapshot_append_count_gc_in_whole_function) ... ok
2026-11-07T07:16:45.8821217Z test_existing_unicode17_full_operation_corpus_through_whole_function (test_u2_function_import_integration.U2FunctionImportIntegrationTests.test_existing_unicode17_full_operation_corpus_through_whole_function) ... ok
2026-11-07T07:16:49.2187371Z test_existing_unicode17_text_concat_counts_gc_in_whole_function (test_u2_function_import_integration.U2FunctionImportIntegrationTests.test_existing_unicode17_text_concat_counts_gc_in_whole_function) ... ok
2026-11-07T07:16:52.3981016Z test_mixed_list_cannot_masquerade_as_identity_descriptor (test_u2_function_import_integration.U2FunctionImportIntegrationTests.test_mixed_list_cannot_masquerade_as_identity_descriptor) ... ok
2026-11-07T07:16:55.6074450Z test_mixed_text_list_calls_share_exact_whole_function_root_map (test_u2_function_import_integration.U2FunctionImportIntegrationTests.test_mixed_text_list_calls_share_exact_whole_function_root_map) ... ok
2026-11-07T07:17:01.9362293Z test_original_list_get_bounds_independently_keep_source_location (test_u2_function_import_integration.U2FunctionImportIntegrationTests.test_original_list_get_bounds_independently_keep_source_location) ... ok
2026-11-07T07:17:18.5440088Z test_original_list_index_and_replace_snapshot_semantics (test_u2_function_import_integration.U2FunctionImportIntegrationTests.test_original_list_index_and_replace_snapshot_semantics) ... ok
2026-11-07T07:17:24.7874042Z test_original_list_index_bounds_faults_keep_source_location (test_u2_function_import_integration.U2FunctionImportIntegrationTests.test_original_list_index_bounds_faults_keep_source_location) ... ok
2026-11-07T07:17:27.9931084Z test_text_without_forced_block_gc_is_still_valid (test_u2_function_import_integration.U2FunctionImportIntegrationTests.test_text_without_forced_block_gc_is_still_valid) ... ok
2026-11-07T07:17:31.0789917Z test_wrong_list_effects_refused_before_native_assembly (test_u2_function_import_integration.U2FunctionImportIntegrationTests.test_wrong_list_effects_refused_before_native_assembly) ... ok
2026-11-07T07:17:34.1914657Z test_wrong_text_import_version_refused_before_native_assembly (test_u2_function_import_integration.U2FunctionImportIntegrationTests.test_wrong_text_import_version_refused_before_native_assembly) ... ok
2026-11-07T07:17:39.9372410Z test_checked_failure_keeps_identity_cycle_through_gc_and_releases (test_u2_identity_gc_cleanup.U2IdentityGCCleanupTests.test_checked_failure_keeps_identity_cycle_through_gc_and_releases) ... ok
2026-11-07T07:17:39.9775851Z test_two_alias_roots_keep_cyclic_graph_until_last_release (test_u2_identity_gc_cleanup.U2IdentityGCCleanupTests.test_two_alias_roots_keep_cyclic_graph_until_last_release) ... ok
2026-11-07T07:17:46.0358733Z test_two_identity_aliases_survive_checked_cleanup_and_ordered_failures (test_u2_identity_file_cleanup.U2IdentityFileCleanupTests.test_two_identity_aliases_survive_checked_cleanup_and_ordered_failures) ... ok
2026-11-07T07:18:03.6330311Z test_canonical_list_snapshots_native_roots_and_bounds (test_u2_list_i64.U2ListI64Tests.test_canonical_list_snapshots_native_roots_and_bounds) ... ok
2026-11-07T07:18:06.1762749Z test_cfg_instruction_roots_retire_before_native_collection (test_u2_list_i64.U2ListI64Tests.test_cfg_instruction_roots_retire_before_native_collection) ... ok
2026-11-07T07:18:16.2747978Z test_loop_carried_snapshots_and_parallel_swap (test_u2_list_i64.U2ListI64Tests.test_loop_carried_snapshots_and_parallel_swap) ... ok
2026-11-07T07:18:18.7602940Z test_malformed_cfg_edge_emits_nothing (test_u2_list_i64.U2ListI64Tests.test_malformed_cfg_edge_emits_nothing) ... ok
2026-11-07T07:18:31.1422357Z test_malformed_profile_emits_no_native_assembly (test_u2_list_i64.U2ListI64Tests.test_malformed_profile_emits_no_native_assembly) ... ok
2026-11-07T07:18:36.1313814Z test_native_bounds_and_allocation_failure_are_terminal (test_u2_list_i64.U2ListI64Tests.test_native_bounds_and_allocation_failure_are_terminal) ... ok
2026-11-07T07:18:38.6272809Z test_runtime_descriptors_and_independent_frame_layout (test_u2_list_i64.U2ListI64Tests.test_runtime_descriptors_and_independent_frame_layout) ... ok
2026-11-07T07:18:59.6004375Z test_all_text_view_bounds_are_terminal_and_exact (test_u2_text_unicode17.U2TextUnicode17Tests.test_all_text_view_bounds_are_terminal_and_exact) ... ok
2026-11-07T07:19:04.5815774Z test_conservative_text_roots_survive_cfg_loop_backedges_and_gc (test_u2_text_unicode17.U2TextUnicode17Tests.test_conservative_text_roots_survive_cfg_loop_backedges_and_gc) ... ok
2026-11-07T07:19:09.4631819Z test_malformed_descriptor_and_import_refuse_before_assembly (test_u2_text_unicode17.U2TextUnicode17Tests.test_malformed_descriptor_and_import_refuse_before_assembly) ... ok
2026-11-07T07:19:11.9789577Z test_precise_cfg_text_root_retirement_before_collection (test_u2_text_unicode17.U2TextUnicode17Tests.test_precise_cfg_text_root_retirement_before_collection) ... ok
2026-11-07T07:19:14.6719939Z test_recursive_text_frames_keep_caller_roots_across_gc (test_u2_text_unicode17.U2TextUnicode17Tests.test_recursive_text_frames_keep_caller_roots_across_gc) ... ok
2026-11-07T07:19:17.1806521Z test_surrogate_scalar_terminal_fault (test_u2_text_unicode17.U2TextUnicode17Tests.test_surrogate_scalar_terminal_fault) ... ok
2026-11-07T07:19:59.5572777Z test_unicode17_text_counts_copy_scalar_equality_and_gc (test_u2_text_unicode17.U2TextUnicode17Tests.test_unicode17_text_counts_copy_scalar_equality_and_gc) ... ok
2026-11-07T07:19:59.6978864Z test_identity_collisions_reanalysis_and_synthetic_nodes (test_source_fact_index.SourceFactIndexTests.test_identity_collisions_reanalysis_and_synthetic_nodes) ... ok
2026-11-07T07:19:59.6989145Z test_universal_ir_contains_function_contract_and_call (test_universal_ir.UniversalIRTests.test_universal_ir_contains_function_contract_and_call) ... ok
2026-11-07T07:19:59.6998081Z test_universal_ir_has_explicit_checked_arithmetic_and_control_flow (test_universal_ir.UniversalIRTests.test_universal_ir_has_explicit_checked_arithmetic_and_control_flow) ... ok
2026-11-07T07:20:00.6510785Z test_accounting_metadata_and_builder_on_c_bootstrap (test_u1_foundation.U1FoundationTests.test_accounting_metadata_and_builder_on_c_bootstrap) ... ok
2026-11-07T07:20:00.6511998Z test_opcode_categories_and_inline_edges_are_explicit (test_u1_foundation.U1FoundationTests.test_opcode_categories_and_inline_edges_are_explicit)
2026-11-07T07:20:00.7381805Z Future opcodes must never be mistaken for construction cells or CFG edges. ... ok
2026-11-07T07:20:01.1724670Z test_current_radix_paths_and_exact_failure_charges_on_both_runtimes (test_u1_words_path.U1WordPathTests.test_current_radix_paths_and_exact_failure_charges_on_both_runtimes) ... ok
2026-11-07T07:20:01.1725964Z test_compiler_trace_maps_source_symbols_and_entry (test_u1b_profile_decoder.U1BProfileDecoderTests.test_compiler_trace_maps_source_symbols_and_entry) ... ok
2026-11-07T07:20:01.1727185Z test_raw_units_reconcile_across_repeated_phases (test_u1b_profile_decoder.U1BProfileDecoderTests.test_raw_units_reconcile_across_repeated_phases) ... ok
2026-11-07T07:20:01.1728714Z test_rejects_incomplete_unknown_and_nonmonotonic_records (test_u1b_profile_decoder.U1BProfileDecoderTests.test_rejects_incomplete_unknown_and_nonmonotonic_records) ... ok
2026-11-07T07:20:02.7500677Z test_direct_call_declarations_and_verifier (test_u1_calls.U1CallContracts.test_direct_call_declarations_and_verifier) ... ok
2026-11-07T07:20:04.3940924Z test_declarations_bind_exact_verified_bodies (test_u1_module.U1ModuleBindingTests.test_declarations_bind_exact_verified_bodies) ... ok
2026-11-07T07:20:06.4980029Z test_recursive_frames_effects_and_versioned_imports (test_u1_execution.U1CallExecutionTests.test_recursive_frames_effects_and_versioned_imports) ... ok
2026-11-07T07:20:09.5930793Z test_changed_foreign_floating_environment_is_rejected_and_restored (test_u1_native.U1NativeTests.test_changed_foreign_floating_environment_is_rejected_and_restored) ... ok
2026-11-07T07:20:09.6160589Z test_native_adapter_rejects_fast_math (test_u1_native.U1NativeTests.test_native_adapter_rejects_fast_math) ... ok
2026-11-07T07:20:09.6421120Z test_native_float_rational_oracle_and_hostile_environments (test_u1_native.U1NativeTests.test_native_float_rational_oracle_and_hostile_environments) ... ok
2026-11-07T07:20:09.6528938Z test_native_integer_oracle_multivalue_and_parallel_switch_edges (test_u1_native.U1NativeTests.test_native_integer_oracle_multivalue_and_parallel_switch_edges) ... ok
2026-11-07T07:20:09.6658961Z test_native_production_imports_fault_origins_limits_and_strip (test_u1_native.U1NativeTests.test_native_production_imports_fault_origins_limits_and_strip) ... ok
2026-11-07T07:20:09.7804611Z test_native_recursion_and_independent_simplification (test_u1_native.U1NativeTests.test_native_recursion_and_independent_simplification) ... ok
2026-11-07T07:20:09.7924871Z test_publication_invalidation_and_transactional_simplification (test_u1_native.U1NativeTests.test_publication_invalidation_and_transactional_simplification) ... ok
2026-11-07T07:20:09.7999783Z test_source_map_ingress_remap_and_stale_excerpt (test_u1_native.U1NativeTests.test_source_map_ingress_remap_and_stale_excerpt) ... ok
2026-11-07T07:20:09.8053047Z test_test_only_imports_cannot_authorize_production_native_execution (test_u1_native.U1NativeTests.test_test_only_imports_cannot_authorize_production_native_execution) ... ok
2026-11-07T07:20:12.7405297Z test_integer_recursion_switch_promotion_and_fault_traces (test_u1_integer_execution.U1IntegerExecutionTests.test_integer_recursion_switch_promotion_and_fault_traces) ... ok
2026-11-07T07:20:20.8750290Z test_independent_canonical_narrow_execution_and_faults (test_u1_narrow_execution.U1NarrowExecutionTests.test_independent_canonical_narrow_execution_and_faults) ... ok
2026-11-07T07:20:21.4117826Z test_native_owned_type_graph_and_independent_verifier (test_u1_aggregate_graph.U1AggregateTypeGraphTests.test_native_owned_type_graph_and_independent_verifier) ... ok
2026-11-07T07:20:22.0585953Z test_immutable_make_get_set_against_python_value_copy_oracle (test_u1_aggregate_values.U1AggregateValuesTests.test_immutable_make_get_set_against_python_value_copy_oracle) ... ok
2026-11-07T07:20:23.8731036Z test_canonical_aggregate_operations_and_independent_dead_code_verifier (test_u1_aggregate_ssa.U1AggregateSSATests.test_canonical_aggregate_operations_and_independent_dead_code_verifier) ... ok
2026-11-07T07:20:25.7866129Z test_verified_canonical_ssa_immutable_execution (test_u1_aggregate_execution.U1AggregateExecutionTests.test_verified_canonical_ssa_immutable_execution) ... ok
2026-11-07T07:20:27.7684956Z test_native_verified_canonical_aggregate_oracle (test_u1_aggregate_canonical_oracle.U1CanonicalAggregateOracleTests.test_native_verified_canonical_aggregate_oracle) ... ok
2026-11-07T07:20:29.9253680Z test_canonical_aggregate_signature_cfg_and_promotion (test_u1_aggregate_signatures.U1AggregateSignatureTests.test_canonical_aggregate_signature_cfg_and_promotion) ... ok
2026-11-07T07:20:31.9117250Z test_canonical_aggregate_loop_reentry_and_fuel (test_u1_aggregate_loops.U1AggregateLoopTests.test_canonical_aggregate_loop_reentry_and_fuel) ... ok
2026-11-07T07:20:34.1284688Z test_linked_canonical_aggregate_calls_and_first_fault (test_u1_aggregate_calls.U1AggregateCallTests.test_linked_canonical_aggregate_calls_and_first_fault) ... ok
2026-11-07T07:20:37.1416100Z test_actual_aggregate_owner_backing_and_gc_reclamation (test_u1b_actual_physical.U1BAggregatePhysicalTests.test_actual_aggregate_owner_backing_and_gc_reclamation) ... U1B_OWNER_PHYSICAL={"actual_after_gc": {"function": {"live": 0, "objects": 60, "observed_bytes": 22592, "reclaimed_bytes": 22592, "reclaimed_objects": 60}, "metadata": {"live": 0, "objects": 116, "observed_bytes": 44480, "reclaimed_bytes": 44480, "reclaimed_objects": 116}}, "actual_before_gc": {"function": {"live": 1152, "objects": 60, "observed_bytes": 22592, "reclaimed_bytes": 21440, "reclaimed_objects": 54}, "metadata": {"live": 512, "objects": 116, "observed_bytes": 44480, "reclaimed_bytes": 43968, "reclaimed_objects": 112}}, "measurement_scope": "U1b immutable type graph and reference value-engine only; no canonical whole compiler RSS", "owner_request_peak_traffic": {"function": [45408, 68128], "metadata": [129632, 129632]}, "structural_backing": {"function": [30, 17760, 960, 18720], "metadata": [58, 35136, 1856, 36992]}}
2026-11-07T07:20:37.1421850Z ok
2026-11-07T07:20:40.5547043Z test_owned_actual_capacity_by_owner_and_gc_reclamation (test_u1_owner_physical.U1OwnerPhysicalTests.test_owned_actual_capacity_by_owner_and_gc_reclamation) ... U1A_OWNER_TIMING={"stage": "owner-physical-c", "wall_seconds": 0.007270195000046442}
2026-11-07T07:20:45.2489062Z U1A_OWNER_TIMING={"stage": "owner-physical-owned", "wall_seconds": 4.6942130630000065}
2026-11-07T07:20:49.9912680Z U1A_OWNER_TIMING={"stage": "owner-physical-owned-diagnostic", "wall_seconds": 4.730397250999999}
2026-11-07T07:20:49.9922709Z U1A_OWNER_ACTUAL={"after_gc": {"backing": {"function": {"live": 0, "objects": 256, "observed_bytes": 91744, "reclaimed_bytes": 91744, "reclaimed_objects": 256}, "metadata": {"live": 0, "objects": 420, "observed_bytes": 154656, "reclaimed_bytes": 154656, "reclaimed_objects": 420}, "request": {"live": 0, "objects": 0, "observed_bytes": 0, "reclaimed_bytes": 0, "reclaimed_objects": 0}, "scratch": {"live": 0, "objects": 2668, "observed_bytes": 1048112, "reclaimed_bytes": 1048112, "reclaimed_objects": 2668}, "stress": {"live": 0, "objects": 16938, "observed_bytes": 6654304, "reclaimed_bytes": 6654304, "reclaimed_objects": 16938}}, "error": 0, "owners": {"function": {"allocations": 629, "live": 0, "peak": 95168, "reclaimed_bytes": 171648, "reclaimed_objects": 629, "traffic": 171648}, "metadata": {"allocations": 7305, "live": 0, "peak": 393456, "reclaimed_bytes": 1638624, "reclaimed_objects": 7305, "traffic": 1638624}, "request": {"allocations": 2, "live": 0, "peak": 640, "reclaimed_bytes": 640, "reclaimed_objects": 2, "traffic": 640}, "scratch": {"allocations": 11454, "live": 0, "peak": 1311984, "reclaimed_bytes": 3479472, "reclaimed_objects": 11454, "traffic": 3479472}, "stress": {"allocations": 72723, "live": 0, "peak": 7858416, "reclaimed_bytes": 21974448, "reclaimed_objects": 72723, "traffic": 21974448}}}, "before_gc": {"backing": {"function": {"live": 91744, "objects": 256, "observed_bytes": 91744, "reclaimed_bytes": 0, "reclaimed_objects": 0}, "metadata": {"live": 154656, "objects": 420, "observed_bytes": 154656, "reclaimed_bytes": 0, "reclaimed_objects": 0}, "request": {"live": 0, "objects": 0, "observed_bytes": 0, "reclaimed_bytes": 0, "reclaimed_objects": 0}, "scratch": {"live": 1088, "objects": 2668, "observed_bytes": 1048112, "reclaimed_bytes": 1047024, "reclaimed_objects": 2664}, "stress": {"live": 6654304, "objects": 16938, "observed_bytes": 6654304, "reclaimed_bytes": 0, "reclaimed_objects": 0}}, "error": 0, "owners": {"function": {"allocations": 629, "live": 64992, "peak": 95168, "reclaimed_bytes": 106656, "reclaimed_objects": 397, "traffic": 171648}, "metadata": {"allocations": 7305, "live": 287168, "peak": 393456, "reclaimed_bytes": 1351456, "reclaimed_objects": 6260, "traffic": 1638624}, "request": {"allocations": 2, "live": 128, "peak": 640, "reclaimed_bytes": 512, "reclaimed_objects": 1, "traffic": 640}, "scratch": {"allocations": 11454, "live": 2560, "peak": 1311984, "reclaimed_bytes": 3476912, "reclaimed_objects": 11443, "traffic": 3479472}, "stress": {"allocations": 72723, "live": 7765936, "peak": 7858416, "reclaimed_bytes": 14208512, "reclaimed_objects": 47227, "traffic": 21974448}}}}
2026-11-07T07:20:49.9929589Z ok
2026-11-07T07:20:50.0003214Z test_owned_layout_contract_and_independent_large_radix_oracle (test_u1_owner_physical.U1OwnerPhysicalTests.test_owned_layout_contract_and_independent_large_radix_oracle) ... U1A_OWNER_TIMING={"stage": "owner-physical-c", "wall_seconds": 0.007389861999968161}
2026-11-07T07:20:50.0004087Z ok
2026-11-07T07:20:50.0006020Z test_prior_c_heap_evidence_remains_independent_not_a_multiplier (test_u1_owner_physical.U1OwnerPhysicalTests.test_prior_c_heap_evidence_remains_independent_not_a_multiplier) ... ok
2026-11-07T07:20:50.3531552Z test_native_handler_and_abandoned_call_allocations_are_reclaimed (test_native_runtime_lifetimes.NativeRuntimeLifetimeTests.test_native_handler_and_abandoned_call_allocations_are_reclaimed) ... ok
2026-11-07T07:20:51.3011535Z test_large_heap_interval_and_empty_heap_reset (test_heap_scaled_collection.HeapScaledCollectionTests.test_large_heap_interval_and_empty_heap_reset) ... ok
2026-11-07T07:20:52.2022168Z test_allocator_size_bitmap_high_bit_multiple_heads_and_release_reset (test_runtime_lookup_caches.IdentityBackingCacheTests.test_allocator_size_bitmap_high_bit_multiple_heads_and_release_reset) ... ok
2026-11-07T07:20:52.2433191Z test_allocator_split_reuses_tail_and_preserves_small_remainder (test_runtime_lookup_caches.IdentityBackingCacheTests.test_allocator_split_reuses_tail_and_preserves_small_remainder) ... ok
2026-11-07T07:20:52.2837221Z test_identity_cache_forced_hash_collisions_and_invalidation_holes (test_runtime_lookup_caches.IdentityBackingCacheTests.test_identity_cache_forced_hash_collisions_and_invalidation_holes) ... ok
2026-11-07T07:20:52.3239467Z test_identity_writes_preserve_value_snapshots_escaped_refs_and_gc (test_runtime_lookup_caches.IdentityBackingCacheTests.test_identity_writes_preserve_value_snapshots_escaped_refs_and_gc) ... ok
2026-11-07T07:20:57.5534532Z test_optional_identity_updates_preserve_aliases_rebinding_and_nested_snapshots (test_freestanding_graph_values.FreestandingGraphValueTests.test_optional_identity_updates_preserve_aliases_rebinding_and_nested_snapshots) ... ok
2026-11-07T07:20:57.9380114Z test_u2_managed_unicode17_list_value_and_identity_alias_parity (test_freestanding_graph_values.FreestandingGraphValueTests.test_u2_managed_unicode17_list_value_and_identity_alias_parity) ... ok
2026-11-07T07:20:58.8384813Z test_owned_graph_exact_slot_roots_preserve_interior_and_fallback (test_runtime_lookup_caches.RuntimeLookupCacheTests.test_owned_graph_exact_slot_roots_preserve_interior_and_fallback) ... ok
2026-11-07T07:20:58.9177939Z test_owned_slot_scratch_reuse_zeroing_nesting_and_refusal (test_runtime_lookup_caches.RuntimeLookupCacheTests.test_owned_slot_scratch_reuse_zeroing_nesting_and_refusal) ... ok
2026-11-07T07:21:04.2197772Z test_registered_roots_bound_loop_slots_and_preserve_pending_results (test_freestanding_text_roots.FreestandingTextRootTests.test_registered_roots_bound_loop_slots_and_preserve_pending_results) ... ok
2026-11-07T07:21:09.3486607Z test_interior_and_saved_failure_roots_are_validated_and_collected (test_freestanding_graph_values.FreestandingGraphValueTests.test_interior_and_saved_failure_roots_are_validated_and_collected) ... ok
2026-11-07T07:21:09.3896855Z test_u2_saved_failure_root_survives_explicit_gc_and_releases (test_freestanding_graph_values.FreestandingGraphValueTests.test_u2_saved_failure_root_survives_explicit_gc_and_releases) ... ok
2026-11-07T07:21:10.2852696Z test_u2_primary_and_secondary_survive_forced_gc_in_order (test_freestanding_graph_values.FreestandingGraphValueTests.test_u2_primary_and_secondary_survive_forced_gc_in_order) ... ok
2026-11-07T07:21:13.6857005Z test_generated_scoped_bind_publish_release_survives_forced_gc (test_u2_native_root_publish.U2NativeRootPublishTests.test_generated_scoped_bind_publish_release_survives_forced_gc) ... ok
2026-11-07T07:21:18.8199757Z test_canonical_single_owner_checked_edge_gate (test_u2_native_cleanup.U2NativeCleanupTests.test_canonical_single_owner_checked_edge_gate)
2026-11-07T07:21:21.3810455Z Verified UIR checked edge/root/owner must precede File adapter emission. ... ok
2026-11-07T07:21:21.3810998Z test_surviving_prefix_and_pending_scalar_return (test_u2_native_cleanup.U2NativeCleanupTests.test_surviving_prefix_and_pending_scalar_return)
2026-11-07T07:21:22.2204123Z Inner exits do not close outer File; pending i64 cancels on failure. ... ok
2026-11-07T07:21:23.1977208Z test_verified_plan_drives_real_reverse_file_cleanup_and_failure_roots (test_u2_native_cleanup.U2NativeCleanupTests.test_verified_plan_drives_real_reverse_file_cleanup_and_failure_roots) ... ok
2026-11-07T07:21:31.1256859Z test_file_checked_failure_publishes_typed_root_through_forced_gc (test_u2_checked_rooted.U2CheckedRootedTests.test_file_checked_failure_publishes_typed_root_through_forced_gc) ... ok
2026-11-07T07:21:39.2077392Z test_verified_ssa_edges_dispatch_success_and_failure_with_forced_gc (test_u2_checked_ssa.U2CheckedSSATests.test_verified_ssa_edges_dispatch_success_and_failure_with_forced_gc) ... ok
2026-11-07T07:21:47.4664797Z test_canonical_outer_file_owner_moves_on_both_checked_edges (test_u2_checked_ssa_prefix.U2CheckedSSAPrefixTests.test_canonical_outer_file_owner_moves_on_both_checked_edges) ... ok
2026-11-07T07:21:50.6620691Z test_verified_two_stage_native_dispatch_consumes_both_files (test_u2_checked_ssa_prefix.U2CheckedSSAPrefixTests.test_verified_two_stage_native_dispatch_consumes_both_files) ... ok
2026-11-07T07:21:56.7081089Z test_nested_live_frames_preserve_primary_and_ordered_close_failures (test_u2_recursive_native_cleanup.U2RecursiveNativeCleanupTests.test_nested_live_frames_preserve_primary_and_ordered_close_failures) ... ok
2026-11-07T07:21:58.1072901Z test_text_publication_and_shared_capacity_failure_boundaries (test_owned_runtime_allocation_failures.OwnedRuntimeAllocationFailureTests.test_text_publication_and_shared_capacity_failure_boundaries) ... ok
2026-11-07T07:22:00.5124752Z test_malformed_ir_and_budget_protocol (test_u1_verifier.U1VerifierTests.test_malformed_ir_and_budget_protocol) ... ok
2026-11-07T07:22:04.1387624Z test_differential_execution_shapes_and_failure_cleanup (test_u1_promotion.U1PromotionTests.test_differential_execution_shapes_and_failure_cleanup) ... ok
2026-11-07T07:22:04.1388113Z test_switch_physical_samples (test_u1_promotion.U1PromotionTests.test_switch_physical_samples)
2026-11-07T07:22:06.7341148Z Five fresh C-native direct-UIR runs: real process RSS plus owned UIR budgets. ... U1A_SWITCH_PHYSICAL=[{"function_peak_bytes": [162368, 274528, 720704, 162368, 177088], "function_traffic_bytes": [400160, 681056, 1741536, 398592, 441728], "function_work_visits": [13676, 38713, 138775, 12689, 18307], "peak_rss_native_units": 125172, "peak_rss_units": "KiB", "trial": 1, "wall_seconds": 0.027393}, {"function_peak_bytes": [162368, 274528, 720704, 162368, 177088], "function_traffic_bytes": [400160, 681056, 1741536, 398592, 441728], "function_work_visits": [13676, 38713, 138775, 12689, 18307], "peak_rss_native_units": 125172, "peak_rss_units": "KiB", "trial": 2, "wall_seconds": 0.020247}, {"function_peak_bytes": [162368, 274528, 720704, 162368, 177088], "function_traffic_bytes": [400160, 681056, 1741536, 398592, 441728], "function_work_visits": [13676, 38713, 138775, 12689, 18307], "peak_rss_native_units": 125172, "peak_rss_units": "KiB", "trial": 3, "wall_seconds": 0.020206}, {"function_peak_bytes": [162368, 274528, 720704, 162368, 177088], "function_traffic_bytes": [400160, 681056, 1741536, 398592, 441728], "function_work_visits": [13676, 38713, 138775, 12689, 18307], "peak_rss_native_units": 125172, "peak_rss_units": "KiB", "trial": 4, "wall_seconds": 0.020206}, {"function_peak_bytes": [162368, 274528, 720704, 162368, 177088], "function_traffic_bytes": [400160, 681056, 1741536, 398592, 441728], "function_work_visits": [13676, 38713, 138775, 12689, 18307], "peak_rss_native_units": 125172, "peak_rss_units": "KiB", "trial": 5, "wall_seconds": 0.020196}]
2026-11-07T07:22:06.7344576Z ok
2026-11-07T07:22:11.1303330Z test_frozen_successful_programs_match_existing_native_compilers (test_u3_stage0_parity_baseline.U3Stage0ParityBaseline.test_frozen_successful_programs_match_existing_native_compilers) ... ok
2026-11-07T07:22:11.1305730Z
2026-11-07T07:22:11.1305909Z ----------------------------------------------------------------------
2026-11-07T07:22:11.1306214Z Ran 170 tests in 850.922s
2026-11-07T07:22:11.1306339Z
2026-11-07T07:22:11.1306413Z OK (skipped=3)
2026-11-07T07:22:11.1316343Z [CI timing] profile=smoke total=850.92s slowest=[('test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_owned_and_c_bootstrap_generators_emit_identical_checked_function', 90.246), ('test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_owned_and_c_generators_agree_on_direct_group', 86.041), ('test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_closed_group_refusals_precede_all_assembly', 46.999), ('test_u2_text_unicode17.U2TextUnicode17Tests.test_unicode17_text_counts_copy_scalar_equality_and_gc', 42.377), ('test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_malformed_body_and_dead_failure_returns_refuse_before_emission', 30.745)]
2026-11-07T07:22:11.2018294Z ##[group]Run actions/upload-artifact@v6
2026-11-07T07:22:11.2018457Z with:
2026-11-07T07:22:11.2018561Z   name: smoke-1
2026-11-07T07:22:11.2018670Z   retention-days: 14
2026-11-07T07:22:11.2018882Z   path: /home/runner/work/_temp/test-results.json
/home/runner/work/_temp/test-results.log

2026-11-07T07:22:11.2019122Z   if-no-files-found: warn
2026-11-07T07:22:11.2019245Z   compression-level: 6
2026-11-07T07:22:11.2019361Z   overwrite: false
2026-11-07T07:22:11.2019478Z   include-hidden-files: false
2026-11-07T07:22:11.2019601Z env:
2026-11-07T07:22:11.2019697Z   CC: clang
2026-11-07T07:22:11.2019797Z   CFLAGS: -O2
2026-11-07T07:22:11.2019952Z   pythonLocation: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:22:11.2020177Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib/pkgconfig
2026-11-07T07:22:11.2020397Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:22:11.2020595Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:22:11.2020805Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:22:11.2021004Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib
2026-11-07T07:22:11.2021173Z ##[endgroup]
2026-11-07T07:22:11.3001317Z Multiple search paths detected. Calculating the least common ancestor of all paths
2026-11-07T07:22:11.3021491Z The least common ancestor is /home/runner/work/_temp. This will be the root directory of the artifact
2026-11-07T07:22:11.3021943Z With the provided path, there will be 2 files uploaded
2026-11-07T07:22:11.3022359Z Artifact name is valid!
2026-11-07T07:22:11.3022570Z Root directory input is valid!
2026-11-07T07:22:11.6316481Z Beginning upload of artifact content to blob storage
2026-11-07T07:22:11.8666268Z Uploaded bytes 8020
2026-11-07T07:22:11.9266957Z Finished uploading artifact content to blob storage!
2026-11-07T07:22:11.9267531Z SHA256 digest of uploaded artifact zip is 3dd11d4725296bdf1eaed932184516a044352703e03b728c4d0a18a1106a82ff
2026-11-07T07:22:11.9269030Z Finalizing artifact upload
2026-11-07T07:22:12.4614891Z Artifact smoke-1.zip successfully finalized. Artifact ID 13565457561
2026-11-07T07:22:12.4615564Z Artifact smoke-1 has been successfully uploaded! Final size is 8020 bytes. Artifact ID is 13565457561
2026-11-07T07:22:12.4618113Z Artifact download URL: https://github.com/eristavi/eristavi-lang/actions/runs/42349932257/artifacts/13565457561
2026-11-07T07:22:12.4759196Z Post job cleanup.
2026-11-07T07:22:12.5613217Z Post job cleanup.
2026-11-07T07:22:12.6177833Z [command]/usr/bin/git version
2026-11-07T07:22:12.6209673Z git version 2.56.0
2026-11-07T07:22:12.6235077Z Temporarily overriding HOME='/home/runner/work/_temp/d2d7b624-ef56-4a3e-a2b2-684bc6651ba8' before making global git config changes
2026-11-07T07:22:12.6236173Z Adding repository directory to the temporary git global config as a safe directory
2026-11-07T07:22:12.6238754Z [command]/usr/bin/git config --global --add safe.directory /home/runner/work/eristavi-lang/eristavi-lang
2026-11-07T07:22:12.6266958Z Removing SSH command configuration
2026-11-07T07:22:12.6271344Z [command]/usr/bin/git config --local --name-only --get-regexp core\.sshCommand
2026-11-07T07:22:12.6299480Z [command]/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'core\.sshCommand' && git config --local --unset-all 'core.sshCommand' || :"
2026-11-07T07:22:12.6495190Z Removing HTTP extra header
2026-11-07T07:22:12.6499308Z [command]/usr/bin/git config --local --name-only --get-regexp http\.https\:\/\/github\.com\/\.extraheader
2026-11-07T07:22:12.6527884Z [command]/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'http\.https\:\/\/github\.com\/\.extraheader' && git config --local --unset-all 'http.https://github.com/.extraheader' || :"
2026-11-07T07:22:12.6716439Z Removing includeIf entries pointing to credentials config files
2026-11-07T07:22:12.6724386Z [command]/usr/bin/git config --local --name-only --get-regexp ^includeIf\.gitdir:
2026-11-07T07:22:12.6765685Z includeif.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git.path
2026-11-07T07:22:12.6775829Z includeif.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git/worktrees/*.path
2026-11-07T07:22:12.6793269Z includeif.gitdir:/github/workspace/.git.path
2026-11-07T07:22:12.6793766Z includeif.gitdir:/github/workspace/.git/worktrees/*.path
2026-11-07T07:22:12.6795017Z [command]/usr/bin/git config --local --get-all includeif.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git.path
2026-11-07T07:22:12.6814858Z /home/runner/work/_temp/git-credentials-579fd627-0dbc-4629-990f-24eb2c95d6ac.config
2026-11-07T07:22:12.6836097Z [command]/usr/bin/git config --local --unset includeif.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git.path /home/runner/work/_temp/git-credentials-579fd627-0dbc-4629-990f-24eb2c95d6ac.config
2026-11-07T07:22:12.6887466Z [command]/usr/bin/git config --local --get-all includeif.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git/worktrees/*.path
2026-11-07T07:22:12.6909592Z /home/runner/work/_temp/git-credentials-579fd627-0dbc-4629-990f-24eb2c95d6ac.config
2026-11-07T07:22:12.6917835Z [command]/usr/bin/git config --local --unset includeif.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git/worktrees/*.path /home/runner/work/_temp/git-credentials-579fd627-0dbc-4629-990f-24eb2c95d6ac.config
2026-11-07T07:22:12.6959217Z [command]/usr/bin/git config --local --get-all includeif.gitdir:/github/workspace/.git.path
2026-11-07T07:22:12.6987804Z /github/runner_temp/git-credentials-579fd627-0dbc-4629-990f-24eb2c95d6ac.config
2026-11-07T07:22:12.6994251Z [command]/usr/bin/git config --local --unset includeif.gitdir:/github/workspace/.git.path /github/runner_temp/git-credentials-579fd627-0dbc-4629-990f-24eb2c95d6ac.config
2026-11-07T07:22:12.7030585Z [command]/usr/bin/git config --local --get-all includeif.gitdir:/github/workspace/.git/worktrees/*.path
2026-11-07T07:22:12.7057928Z /github/runner_temp/git-credentials-579fd627-0dbc-4629-990f-24eb2c95d6ac.config
2026-11-07T07:22:12.7063588Z [command]/usr/bin/git config --local --unset includeif.gitdir:/github/workspace/.git/worktrees/*.path /github/runner_temp/git-credentials-579fd627-0dbc-4629-990f-24eb2c95d6ac.config
2026-11-07T07:22:12.7104601Z [command]/usr/bin/git submodule foreach --recursive git config --local --show-origin --name-only --get-regexp remote.origin.url
2026-11-07T07:22:12.7299734Z Removing credentials config '/home/runner/work/_temp/git-credentials-579fd627-0dbc-4629-990f-24eb2c95d6ac.config'
2026-11-07T07:22:12.7450209Z Cleaning up orphan processes

````
