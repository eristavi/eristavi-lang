````text
﻿2026-11-07T07:07:31.1515818Z Current runner version: '2.338.2'
2026-11-07T07:07:31.1540582Z ##[group]Runner Image Provisioner
2026-11-07T07:07:31.1541509Z Hosted Compute Agent
2026-11-07T07:07:31.1542215Z Version: 20261028.624
2026-11-07T07:07:31.1543250Z Commit: 54898b74c23fde5556c9b3c3a2290865feef0dfe
2026-11-07T07:07:31.1544110Z Build Date: 2026-10-28T21:51:42Z
2026-11-07T07:07:31.1544884Z Worker ID: {da1ca19b-a388-4d49-9254-b95abf214b88}
2026-11-07T07:07:31.1545617Z Region: westus
2026-11-07T07:07:31.1546223Z Cloud: Azure
2026-11-07T07:07:31.1546880Z ##[endgroup]
2026-11-07T07:07:31.1548430Z ##[group]Operating System
2026-11-07T07:07:31.1549194Z Ubuntu
2026-11-07T07:07:31.1549779Z 24.04.5
2026-11-07T07:07:31.1550335Z LTS
2026-11-07T07:07:31.1550886Z ##[endgroup]
2026-11-07T07:07:31.1551453Z ##[group]Runner Image
2026-11-07T07:07:31.1552189Z Image: ubuntu-24.04
2026-11-07T07:07:31.1552771Z Version: 20261101.360.1
2026-11-07T07:07:31.1554696Z Included Software: https://github.com/actions/runner-images/blob/ubuntu24/20261101.360/images/ubuntu/Ubuntu2404-Readme.md
2026-11-07T07:07:31.1556302Z Image Release: https://github.com/actions/runner-images/releases/tag/ubuntu24%2F20261101.360
2026-11-07T07:07:31.1557399Z ##[endgroup]
2026-11-07T07:07:31.1558522Z ##[group]GITHUB_TOKEN Permissions
2026-11-07T07:07:31.1560490Z Contents: read
2026-11-07T07:07:31.1561188Z Metadata: read
2026-11-07T07:07:31.1561853Z ##[endgroup]
2026-11-07T07:07:31.1564733Z Secret source: Actions
2026-11-07T07:07:31.1565803Z Cache mode: write
2026-11-07T07:07:31.1566728Z Prepare workflow directory
2026-11-07T07:07:31.2030112Z Prepare all required actions
2026-11-07T07:07:31.2079146Z Getting action download info
2026-11-07T07:07:31.5504222Z Download action repository 'actions/checkout@v6' (SHA:d23441a48e516b6c34aea4fa41551a30e30af803)
2026-11-07T07:07:31.6480222Z Download action repository 'actions/setup-python@v6' (SHA:ece7cb06caefa5fff74198d8649806c4678c61a1)
2026-11-07T07:07:31.7211091Z Download action repository 'actions/upload-artifact@v6' (SHA:b7c566a772e6b6bfb58ed0dc250532a479d7789f)
2026-11-07T07:07:31.9229380Z Complete job name: managed-function
2026-11-07T07:07:32.0099900Z ##[group]Run actions/checkout@v6
2026-11-07T07:07:32.0100782Z with:
2026-11-07T07:07:32.0101251Z   repository: eristavi/eristavi-lang
2026-11-07T07:07:32.0105390Z   token: ***
2026-11-07T07:07:32.0105823Z   ssh-strict: true
2026-11-07T07:07:32.0106256Z   ssh-user: git
2026-11-07T07:07:32.0106701Z   persist-credentials: true
2026-11-07T07:07:32.0107189Z   clean: true
2026-11-07T07:07:32.0107626Z   sparse-checkout-cone-mode: true
2026-11-07T07:07:32.0108149Z   fetch-depth: 1
2026-11-07T07:07:32.0108575Z   fetch-tags: false
2026-11-07T07:07:32.0109017Z   show-progress: true
2026-11-07T07:07:32.0109459Z   lfs: false
2026-11-07T07:07:32.0109873Z   submodules: false
2026-11-07T07:07:32.0110318Z   set-safe-directory: true
2026-11-07T07:07:32.0110816Z   allow-unsafe-pr-checkout: false
2026-11-07T07:07:32.0111577Z env:
2026-11-07T07:07:32.0111985Z   CC: clang
2026-11-07T07:07:32.0112406Z   CFLAGS: -O2
2026-11-07T07:07:32.0113004Z ##[endgroup]
2026-11-07T07:07:32.3490001Z Syncing repository: eristavi/eristavi-lang
2026-11-07T07:07:32.3491888Z ##[group]Getting Git version info
2026-11-07T07:07:32.3492697Z Working directory is '/home/runner/work/eristavi-lang/eristavi-lang'
2026-11-07T07:07:32.3494229Z [command]/usr/bin/git version
2026-11-07T07:07:32.3608459Z git version 2.56.0
2026-11-07T07:07:32.3632035Z ##[endgroup]
2026-11-07T07:07:32.3647813Z Temporarily overriding HOME='/home/runner/work/_temp/db9dc44c-c9e0-4c38-a46e-7932235fa2be' before making global git config changes
2026-11-07T07:07:32.3650186Z Adding repository directory to the temporary git global config as a safe directory
2026-11-07T07:07:32.3653606Z [command]/usr/bin/git config --global --add safe.directory /home/runner/work/eristavi-lang/eristavi-lang
2026-11-07T07:07:32.3724057Z Deleting the contents of '/home/runner/work/eristavi-lang/eristavi-lang'
2026-11-07T07:07:32.3735148Z ##[group]Determining repository object format
2026-11-07T07:07:32.3746548Z ##[endgroup]
2026-11-07T07:07:32.3748060Z ##[group]Initializing the repository
2026-11-07T07:07:32.3749361Z [command]/usr/bin/git init /home/runner/work/eristavi-lang/eristavi-lang
2026-11-07T07:07:32.3877940Z hint: Using 'master' as the name for the initial branch. This default branch name
2026-11-07T07:07:32.3879857Z hint: will change to "main" in Git 3.0. To configure the initial branch name
2026-11-07T07:07:32.3881240Z hint: to use in all of your new repositories, which will suppress this warning,
2026-11-07T07:07:32.3882285Z hint: call:
2026-11-07T07:07:32.3882835Z hint:
2026-11-07T07:07:32.3883768Z hint: 	git config --global init.defaultBranch <name>
2026-11-07T07:07:32.3884411Z hint:
2026-11-07T07:07:32.3885014Z hint: Names commonly chosen instead of 'master' are 'main', 'trunk' and
2026-11-07T07:07:32.3886304Z hint: 'development'. The just-created branch can be renamed via this command:
2026-11-07T07:07:32.3887079Z hint:
2026-11-07T07:07:32.3887509Z hint: 	git branch -m <name>
2026-11-07T07:07:32.3888041Z hint:
2026-11-07T07:07:32.3888689Z hint: Disable this message with "git config set advice.defaultBranchName false"
2026-11-07T07:07:32.3895975Z Initialized empty Git repository in /home/runner/work/eristavi-lang/eristavi-lang/.git/
2026-11-07T07:07:32.3909435Z [command]/usr/bin/git remote add origin https://github.com/eristavi/eristavi-lang
2026-11-07T07:07:32.3962247Z ##[endgroup]
2026-11-07T07:07:32.3963412Z ##[group]Disabling automatic garbage collection
2026-11-07T07:07:32.3966972Z [command]/usr/bin/git config --local gc.auto 0
2026-11-07T07:07:32.4004602Z ##[endgroup]
2026-11-07T07:07:32.4006562Z ##[group]Setting up auth
2026-11-07T07:07:32.4007291Z Removing SSH command configuration
2026-11-07T07:07:32.4022013Z [command]/usr/bin/git config --local --name-only --get-regexp core\.sshCommand
2026-11-07T07:07:32.4074334Z [command]/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'core\.sshCommand' && git config --local --unset-all 'core.sshCommand' || :"
2026-11-07T07:07:32.4505720Z Removing HTTP extra header
2026-11-07T07:07:32.4513799Z [command]/usr/bin/git config --local --name-only --get-regexp http\.https\:\/\/github\.com\/\.extraheader
2026-11-07T07:07:32.4557627Z [command]/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'http\.https\:\/\/github\.com\/\.extraheader' && git config --local --unset-all 'http.https://github.com/.extraheader' || :"
2026-11-07T07:07:32.4819158Z Removing includeIf entries pointing to credentials config files
2026-11-07T07:07:32.4820338Z [command]/usr/bin/git config --local --name-only --get-regexp ^includeIf\.gitdir:
2026-11-07T07:07:32.4864464Z [command]/usr/bin/git submodule foreach --recursive git config --local --show-origin --name-only --get-regexp remote.origin.url
2026-11-07T07:07:32.5112763Z [command]/usr/bin/git config --file /home/runner/work/_temp/git-credentials-588b07d4-b78a-4d0e-857f-b41935bac8a6.config http.https://github.com/.extraheader AUTHORIZATION: basic ***
2026-11-07T07:07:32.5163937Z [command]/usr/bin/git config --local includeIf.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git.path /home/runner/work/_temp/git-credentials-588b07d4-b78a-4d0e-857f-b41935bac8a6.config
2026-11-07T07:07:32.5208353Z [command]/usr/bin/git config --local includeIf.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git/worktrees/*.path /home/runner/work/_temp/git-credentials-588b07d4-b78a-4d0e-857f-b41935bac8a6.config
2026-11-07T07:07:32.5253933Z [command]/usr/bin/git config --local includeIf.gitdir:/github/workspace/.git.path /github/runner_temp/git-credentials-588b07d4-b78a-4d0e-857f-b41935bac8a6.config
2026-11-07T07:07:32.5301669Z [command]/usr/bin/git config --local includeIf.gitdir:/github/workspace/.git/worktrees/*.path /github/runner_temp/git-credentials-588b07d4-b78a-4d0e-857f-b41935bac8a6.config
2026-11-07T07:07:32.5340681Z ##[endgroup]
2026-11-07T07:07:32.5341440Z ##[group]Fetching the repository
2026-11-07T07:07:32.5349195Z [command]/usr/bin/git -c protocol.version=2 fetch --no-tags --prune --no-recurse-submodules --depth=1 origin +43d56f2f526fd57db5d790413217de439858b7a5:refs/remotes/origin/compiler/u2-cleanup-foundation-20261102
2026-11-07T07:07:33.3745263Z From https://github.com/eristavi/eristavi-lang
2026-11-07T07:07:33.3748688Z  * [new ref]         43d56f2f526fd57db5d790413217de439858b7a5 -> origin/compiler/u2-cleanup-foundation-20261102
2026-11-07T07:07:33.3758470Z [command]/usr/bin/git branch --list --remote origin/compiler/u2-cleanup-foundation-20261102
2026-11-07T07:07:33.3796345Z   origin/compiler/u2-cleanup-foundation-20261102
2026-11-07T07:07:33.3806192Z [command]/usr/bin/git rev-parse refs/remotes/origin/compiler/u2-cleanup-foundation-20261102
2026-11-07T07:07:33.3839123Z 43d56f2f526fd57db5d790413217de439858b7a5
2026-11-07T07:07:33.3846941Z ##[endgroup]
2026-11-07T07:07:33.3849194Z ##[group]Determining the checkout info
2026-11-07T07:07:33.3852060Z ##[endgroup]
2026-11-07T07:07:33.3854263Z [command]/usr/bin/git sparse-checkout disable
2026-11-07T07:07:33.3919424Z [command]/usr/bin/git config --local --unset-all extensions.worktreeConfig
2026-11-07T07:07:33.3960382Z ##[group]Checking out the ref
2026-11-07T07:07:33.3964783Z [command]/usr/bin/git checkout --progress --force -B compiler/u2-cleanup-foundation-20261102 refs/remotes/origin/compiler/u2-cleanup-foundation-20261102
2026-11-07T07:07:33.4836924Z Switched to a new branch 'compiler/u2-cleanup-foundation-20261102'
2026-11-07T07:07:33.4843361Z branch 'compiler/u2-cleanup-foundation-20261102' set up to track 'origin/compiler/u2-cleanup-foundation-20261102'.
2026-11-07T07:07:33.4853082Z ##[endgroup]
2026-11-07T07:07:33.4907753Z [command]/usr/bin/git log -1 --format=%H
2026-11-07T07:07:33.4943425Z 43d56f2f526fd57db5d790413217de439858b7a5
2026-11-07T07:07:33.5445968Z ##[group]Run actions/setup-python@v6
2026-11-07T07:07:33.5447334Z with:
2026-11-07T07:07:33.5448246Z   python-version: 3.11
2026-11-07T07:07:33.5449291Z   check-latest: false
2026-11-07T07:07:33.5460256Z   token: ***
2026-11-07T07:07:33.5461258Z   update-environment: true
2026-11-07T07:07:33.5462449Z   allow-prereleases: false
2026-11-07T07:07:33.5463792Z   freethreaded: false
2026-11-07T07:07:33.5464798Z env:
2026-11-07T07:07:33.5465653Z   CC: clang
2026-11-07T07:07:33.5466551Z   CFLAGS: -O2
2026-11-07T07:07:33.5467495Z ##[endgroup]
2026-11-07T07:07:33.6930980Z ##[group]Installed versions
2026-11-07T07:07:33.7047474Z Successfully set up CPython (3.11.18)
2026-11-07T07:07:33.7048542Z ##[endgroup]
2026-11-07T07:07:33.7199075Z ##[group]Run python -m pip install -e .
2026-11-07T07:07:33.7199566Z [36;1mpython -m pip install -e .[0m
2026-11-07T07:07:33.7239775Z shell: /usr/bin/bash -e {0}
2026-11-07T07:07:33.7240120Z env:
2026-11-07T07:07:33.7240368Z   CC: clang
2026-11-07T07:07:33.7240617Z   CFLAGS: -O2
2026-11-07T07:07:33.7240960Z   pythonLocation: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:07:33.7241499Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib/pkgconfig
2026-11-07T07:07:33.7242010Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:07:33.7242518Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:07:33.7243353Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:07:33.7243844Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib
2026-11-07T07:07:33.7244239Z ##[endgroup]
2026-11-07T07:07:34.5867585Z Obtaining file:///home/runner/work/eristavi-lang/eristavi-lang
2026-11-07T07:07:34.5882671Z   Installing build dependencies: started
2026-11-07T07:07:35.4405131Z   Installing build dependencies: finished with status 'done'
2026-11-07T07:07:35.4412604Z   Checking if build backend supports build_editable: started
2026-11-07T07:07:35.8255597Z   Checking if build backend supports build_editable: finished with status 'done'
2026-11-07T07:07:35.8269789Z   Getting requirements to build editable: started
2026-11-07T07:07:36.1654736Z   Getting requirements to build editable: finished with status 'done'
2026-11-07T07:07:36.1664391Z   Preparing editable metadata (pyproject.toml): started
2026-11-07T07:07:36.3443617Z   Preparing editable metadata (pyproject.toml): finished with status 'done'
2026-11-07T07:07:37.0329014Z Collecting regex==2026.9.29 (from eristavi-lang==0.0.1.dev0)
2026-11-07T07:07:37.1039902Z   Downloading regex-2026.9.29-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (40 kB)
2026-11-07T07:07:37.2026374Z Collecting unicodedata2==17.0.0 (from eristavi-lang==0.0.1.dev0)
2026-11-07T07:07:37.2155252Z   Downloading unicodedata2-17.0.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (3.3 kB)
2026-11-07T07:07:37.2317237Z Downloading regex-2026.9.29-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (804 kB)
2026-11-07T07:07:37.3179436Z    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 805.0/805.0 kB 10.5 MB/s  0:00:00
2026-11-07T07:07:37.3310794Z Downloading unicodedata2-17.0.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (531 kB)
2026-11-07T07:07:37.3753661Z    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 531.5/531.5 kB 12.5 MB/s  0:00:00
2026-11-07T07:07:37.3843147Z Building wheels for collected packages: eristavi-lang
2026-11-07T07:07:37.3851000Z   Building editable for eristavi-lang (pyproject.toml): started
2026-11-07T07:07:37.5942090Z   Building editable for eristavi-lang (pyproject.toml): finished with status 'done'
2026-11-07T07:07:37.5948914Z   Created wheel for eristavi-lang: filename=eristavi_lang-0.0.1.dev0-0.editable-py3-none-any.whl size=4073 sha256=04fe16f172251fad6e5bbd2140403981d0c18a0fa14d3cd33cd4dc2dbd4bcbd0
2026-11-07T07:07:37.5950921Z   Stored in directory: /tmp/pip-ephem-wheel-cache-s4uqbagd/wheels/bf/0e/13/3c92c3d16e7da71040fe0218774d6a7875df473d79c0e7b5aa
2026-11-07T07:07:37.5973878Z Successfully built eristavi-lang
2026-11-07T07:07:37.6155984Z Installing collected packages: unicodedata2, regex, eristavi-lang
2026-11-07T07:07:37.7505801Z
2026-11-07T07:07:37.7514606Z Successfully installed eristavi-lang-0.0.1.dev0 regex-2026.9.29 unicodedata2-17.0.0
2026-11-07T07:07:37.7524803Z
2026-11-07T07:07:37.7525358Z [notice] A new release of pip is available: 26.2.2 -> 26.3
2026-11-07T07:07:37.7526161Z [notice] To update, run: pip install --upgrade pip
2026-11-07T07:07:37.8347479Z ##[group]Run python -m compileall -q tests/test_u2_function_managed_native.py tests/test_u2_function_checked_native.py tests/test_u2_function_checked_group.py compiler
2026-11-07T07:07:37.8348717Z [36;1mpython -m compileall -q tests/test_u2_function_managed_native.py tests/test_u2_function_checked_native.py tests/test_u2_function_checked_group.py compiler[0m
2026-11-07T07:07:37.8370923Z shell: /usr/bin/bash -e {0}
2026-11-07T07:07:37.8371210Z env:
2026-11-07T07:07:37.8371398Z   CC: clang
2026-11-07T07:07:37.8371590Z   CFLAGS: -O2
2026-11-07T07:07:37.8371871Z   pythonLocation: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:07:37.8372316Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib/pkgconfig
2026-11-07T07:07:37.8372742Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:07:37.8373312Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:07:37.8373697Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:07:37.8374116Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib
2026-11-07T07:07:37.8374440Z ##[endgroup]
2026-11-07T07:07:38.0073888Z ##[group]Run set -o pipefail
2026-11-07T07:07:38.0074244Z [36;1mset -o pipefail[0m
2026-11-07T07:07:38.0074755Z [36;1mPYTHONPATH=tests python -u -m unittest -v test_u1_words_path 2>&1 | tee "$RUNNER_TEMP/u1a-word-path.log"[0m
2026-11-07T07:07:38.0096230Z shell: /usr/bin/bash -e {0}
2026-11-07T07:07:38.0096491Z env:
2026-11-07T07:07:38.0096679Z   CC: clang
2026-11-07T07:07:38.0096870Z   CFLAGS: -O2
2026-11-07T07:07:38.0097151Z   pythonLocation: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:07:38.0097598Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib/pkgconfig
2026-11-07T07:07:38.0098041Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:07:38.0098608Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:07:38.0098994Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:07:38.0099380Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib
2026-11-07T07:07:38.0099699Z ##[endgroup]
2026-11-07T07:07:54.5491519Z test_current_radix_paths_and_exact_failure_charges_on_both_runtimes (test_u1_words_path.U1WordPathTests.test_current_radix_paths_and_exact_failure_charges_on_both_runtimes) ... ok
2026-11-07T07:07:54.5492453Z
2026-11-07T07:07:54.5493613Z ----------------------------------------------------------------------
2026-11-07T07:07:54.5494504Z Ran 1 test in 16.121s
2026-11-07T07:07:54.5494766Z
2026-11-07T07:07:54.5494884Z OK
2026-11-07T07:07:54.5735621Z ##[group]Run set -o pipefail
2026-11-07T07:07:54.5735955Z [36;1mset -o pipefail[0m
2026-11-07T07:07:54.5736708Z [36;1mPYTHONPATH=tests python -u -m unittest -v test_u2_function_managed_native test_u2_function_checked_native test_u2_function_checked_group 2>&1 | tee "$RUNNER_TEMP/u2-managed-function.log"[0m
2026-11-07T07:07:54.5757988Z shell: /usr/bin/bash -e {0}
2026-11-07T07:07:54.5758241Z env:
2026-11-07T07:07:54.5758417Z   CC: clang
2026-11-07T07:07:54.5758598Z   CFLAGS: -O2
2026-11-07T07:07:54.5758868Z   pythonLocation: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:07:54.5759299Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib/pkgconfig
2026-11-07T07:07:54.5759741Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:07:54.5760131Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:07:54.5760512Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:07:54.5760941Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib
2026-11-07T07:07:54.5761262Z ##[endgroup]
2026-11-07T07:08:12.0105688Z test_mixed_text_and_identity_roots_across_loop_and_return (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_mixed_text_and_identity_roots_across_loop_and_return) ... ok
2026-11-07T07:08:18.6179565Z test_recursive_function_parent_only_text_roots_and_scalar_result (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_recursive_function_parent_only_text_roots_and_scalar_result) ... ok
2026-11-07T07:08:49.4372470Z test_recursive_import_or_mismatched_signature_rejected_before_emission (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_recursive_import_or_mismatched_signature_rejected_before_emission) ... ok
2026-11-07T07:08:55.6379869Z test_recursive_two_managed_results_handoff_before_child_scope_leave (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_recursive_two_managed_results_handoff_before_child_scope_leave) ... ok
2026-11-07T07:09:01.9017234Z test_reject_managed_producer_in_dead_block_before_emission (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_reject_managed_producer_in_dead_block_before_emission) ... ok
2026-11-07T07:09:08.1794693Z test_reject_mismatched_identity_descriptor_before_emission (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_reject_mismatched_identity_descriptor_before_emission) ... ok
2026-11-07T07:09:14.2864376Z test_whole_function_identity_phi_and_gc_with_rooted_return (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_whole_function_identity_phi_and_gc_with_rooted_return) ... ok
2026-11-07T07:09:30.8733196Z test_checked_failure_handler_returns_normal_through_parent_frames (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_failure_handler_returns_normal_through_parent_frames) ... ok
2026-11-07T07:09:37.5877301Z test_checked_no_value_success_and_typed_failure_have_no_fake_result (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_no_value_success_and_typed_failure_have_no_fake_result) ... ok
2026-11-07T07:09:44.3735575Z test_checked_one_scalar_result_and_failure_use_distinct_outcomes (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_one_scalar_result_and_failure_use_distinct_outcomes) ... ok
2026-11-07T07:09:52.8903206Z test_checked_recursion_retains_complete_ordered_secondary_context (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_recursion_retains_complete_ordered_secondary_context) ... ok
2026-11-07T07:10:00.4652305Z test_checked_recursive_normal_failure_edges_roots_and_reclamation (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_recursive_normal_failure_edges_roots_and_reclamation) ... ok
2026-11-07T07:10:07.4053803Z test_checked_two_managed_normal_results_and_failed_result_are_disjoint (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_two_managed_normal_results_and_failed_result_are_disjoint) ... ok
2026-11-07T07:10:11.9628381Z test_failure_return_cannot_bypass_an_active_file_owner (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_failure_return_cannot_bypass_an_active_file_owner) ... ok
2026-11-07T07:11:13.4556617Z test_malformed_body_and_dead_failure_returns_refuse_before_emission (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_malformed_body_and_dead_failure_returns_refuse_before_emission) ... ok
2026-11-07T07:11:20.6756606Z test_missing_native_failure_handoff_or_payload_is_a_terminal_defect (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_missing_native_failure_handoff_or_payload_is_a_terminal_defect) ... ok
2026-11-07T07:13:18.6385926Z test_owned_and_c_bootstrap_generators_emit_identical_checked_function (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_owned_and_c_bootstrap_generators_emit_identical_checked_function) ... U2_CHECKED_OWNED_GENERATOR_SECONDS=103.72751517399996
2026-11-07T07:13:26.0975590Z ok
2026-11-07T07:13:32.1677773Z test_whole_publication_table_refuses_corruption_and_releases_on_refusal (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_whole_publication_table_refuses_corruption_and_releases_on_refusal) ... ok
2026-11-07T07:15:24.9857409Z test_closed_group_refusals_precede_all_assembly (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_closed_group_refusals_precede_all_assembly) ... ok
2026-11-07T07:15:32.7525167Z test_different_member_recovers_failure_into_normal_parent_result (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_different_member_recovers_failure_into_normal_parent_result) ... ok
2026-11-07T07:15:40.2693572Z test_distinct_normal_signatures_and_result_positions (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_distinct_normal_signatures_and_result_positions) ... ok
2026-11-07T07:15:47.8392265Z test_list_value_crosses_mutual_frames_and_preserves_snapshot (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_list_value_crosses_mutual_frames_and_preserves_snapshot) ... ok
2026-11-07T07:15:55.2126230Z test_missing_sibling_handoff_roots_are_terminal_defects (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_missing_sibling_handoff_roots_are_terminal_defects) ... ok
2026-11-07T07:16:03.6935342Z test_mutual_checked_frames_gc_and_independent_source_outcomes (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_mutual_checked_frames_gc_and_independent_source_outcomes) ... ok
2026-11-07T07:16:12.8528207Z test_mutual_frames_preserve_primary_and_ordered_secondary_context (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_mutual_frames_preserve_primary_and_ordered_secondary_context) ... ok
2026-11-07T07:16:20.2754513Z test_mutual_native_frame_stack_bound_and_reclamation (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_mutual_native_frame_stack_bound_and_reclamation) ... U2_MUTUAL_STACK=[{"depth": 0, "function_stack_bytes": 592}, {"depth": 1, "function_stack_bytes": 1184}, {"depth": 5, "function_stack_bytes": 3552}, {"depth": 32, "function_stack_bytes": 19536}, {"depth": 64, "function_stack_bytes": 38480}]
2026-11-07T07:16:20.2756022Z ok
2026-11-07T07:18:24.0291232Z test_owned_and_c_generators_agree_on_direct_group (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_owned_and_c_generators_agree_on_direct_group) ... U2_DIRECT_GROUP_OWNED_GENERATOR_SECONDS=101.624
2026-11-07T07:18:24.1567568Z ok
2026-11-07T07:18:38.5603683Z test_preflight_work_and_capacity_refusal_release_owned_plans (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_preflight_work_and_capacity_refusal_release_owned_plans) ... ok
2026-11-07T07:18:46.2051967Z test_two_managed_results_cross_member_handoff (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_two_managed_results_cross_member_handoff) ... ok
2026-11-07T07:18:46.2231838Z
2026-11-07T07:18:46.2232597Z ----------------------------------------------------------------------
2026-11-07T07:18:46.2235446Z Ran 29 tests in 651.252s
2026-11-07T07:18:46.2235698Z
2026-11-07T07:18:46.2236067Z OK
2026-11-07T07:18:46.2566752Z ##[group]Run actions/upload-artifact@v6
2026-11-07T07:18:46.2567085Z with:
2026-11-07T07:18:46.2567297Z   name: u2-managed-function-1
2026-11-07T07:18:46.2567553Z   retention-days: 14
2026-11-07T07:18:46.2568018Z   path: /home/runner/work/_temp/u2-managed-function.log
/home/runner/work/_temp/u1a-word-path.log

2026-11-07T07:18:46.2568508Z   if-no-files-found: warn
2026-11-07T07:18:46.2568747Z   compression-level: 6
2026-11-07T07:18:46.2568963Z   overwrite: false
2026-11-07T07:18:46.2569188Z   include-hidden-files: false
2026-11-07T07:18:46.2569414Z env:
2026-11-07T07:18:46.2569589Z   CC: clang
2026-11-07T07:18:46.2569781Z   CFLAGS: -O2
2026-11-07T07:18:46.2570041Z   pythonLocation: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:18:46.2570472Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib/pkgconfig
2026-11-07T07:18:46.2570891Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:18:46.2571315Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:18:46.2571697Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:18:46.2572079Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib
2026-11-07T07:18:46.2572403Z ##[endgroup]
2026-11-07T07:18:46.4366157Z Multiple search paths detected. Calculating the least common ancestor of all paths
2026-11-07T07:18:46.4368445Z The least common ancestor is /home/runner/work/_temp. This will be the root directory of the artifact
2026-11-07T07:18:46.4369634Z With the provided path, there will be 2 files uploaded
2026-11-07T07:18:46.4370784Z Artifact name is valid!
2026-11-07T07:18:46.4404159Z Root directory input is valid!
2026-11-07T07:18:46.8345360Z Beginning upload of artifact content to blob storage
2026-11-07T07:18:47.1733431Z Uploaded bytes 1584
2026-11-07T07:18:47.2543491Z Finished uploading artifact content to blob storage!
2026-11-07T07:18:47.2544593Z SHA256 digest of uploaded artifact zip is 741a603bd58d2ccb3a2fec8535140356443375b1c025de4c061d979fe2fe8073
2026-11-07T07:18:47.2547029Z Finalizing artifact upload
2026-11-07T07:18:47.8316548Z Artifact u2-managed-function-1.zip successfully finalized. Artifact ID 13564943743
2026-11-07T07:18:47.8317776Z Artifact u2-managed-function-1 has been successfully uploaded! Final size is 1584 bytes. Artifact ID is 13564943743
2026-11-07T07:18:47.8321916Z Artifact download URL: https://github.com/eristavi/eristavi-lang/actions/runs/42349932276/artifacts/13564943743
2026-11-07T07:18:47.8524516Z Post job cleanup.
2026-11-07T07:18:48.0040401Z Post job cleanup.
2026-11-07T07:18:48.1154645Z [command]/usr/bin/git version
2026-11-07T07:18:48.1211765Z git version 2.56.0
2026-11-07T07:18:48.1272519Z Temporarily overriding HOME='/home/runner/work/_temp/ced6e0b1-2798-470c-afaf-07d1f2c736de' before making global git config changes
2026-11-07T07:18:48.1288905Z Adding repository directory to the temporary git global config as a safe directory
2026-11-07T07:18:48.1290362Z [command]/usr/bin/git config --global --add safe.directory /home/runner/work/eristavi-lang/eristavi-lang
2026-11-07T07:18:48.1344678Z Removing SSH command configuration
2026-11-07T07:18:48.1345641Z [command]/usr/bin/git config --local --name-only --get-regexp core\.sshCommand
2026-11-07T07:18:48.1414240Z [command]/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'core\.sshCommand' && git config --local --unset-all 'core.sshCommand' || :"
2026-11-07T07:18:48.1764287Z Removing HTTP extra header
2026-11-07T07:18:48.1765580Z [command]/usr/bin/git config --local --name-only --get-regexp http\.https\:\/\/github\.com\/\.extraheader
2026-11-07T07:18:48.1855014Z [command]/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'http\.https\:\/\/github\.com\/\.extraheader' && git config --local --unset-all 'http.https://github.com/.extraheader' || :"
2026-11-07T07:18:48.2309746Z Removing includeIf entries pointing to credentials config files
2026-11-07T07:18:48.2310379Z [command]/usr/bin/git config --local --name-only --get-regexp ^includeIf\.gitdir:
2026-11-07T07:18:48.2344986Z includeif.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git.path
2026-11-07T07:18:48.2346438Z includeif.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git/worktrees/*.path
2026-11-07T07:18:48.2347745Z includeif.gitdir:/github/workspace/.git.path
2026-11-07T07:18:48.2348640Z includeif.gitdir:/github/workspace/.git/worktrees/*.path
2026-11-07T07:18:48.2359379Z [command]/usr/bin/git config --local --get-all includeif.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git.path
2026-11-07T07:18:48.2401333Z /home/runner/work/_temp/git-credentials-588b07d4-b78a-4d0e-857f-b41935bac8a6.config
2026-11-07T07:18:48.2415978Z [command]/usr/bin/git config --local --unset includeif.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git.path /home/runner/work/_temp/git-credentials-588b07d4-b78a-4d0e-857f-b41935bac8a6.config
2026-11-07T07:18:48.2472634Z [command]/usr/bin/git config --local --get-all includeif.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git/worktrees/*.path
2026-11-07T07:18:48.2511533Z /home/runner/work/_temp/git-credentials-588b07d4-b78a-4d0e-857f-b41935bac8a6.config
2026-11-07T07:18:48.2523679Z [command]/usr/bin/git config --local --unset includeif.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git/worktrees/*.path /home/runner/work/_temp/git-credentials-588b07d4-b78a-4d0e-857f-b41935bac8a6.config
2026-11-07T07:18:48.2577305Z [command]/usr/bin/git config --local --get-all includeif.gitdir:/github/workspace/.git.path
2026-11-07T07:18:48.2616218Z /github/runner_temp/git-credentials-588b07d4-b78a-4d0e-857f-b41935bac8a6.config
2026-11-07T07:18:48.2629504Z [command]/usr/bin/git config --local --unset includeif.gitdir:/github/workspace/.git.path /github/runner_temp/git-credentials-588b07d4-b78a-4d0e-857f-b41935bac8a6.config
2026-11-07T07:18:48.2683731Z [command]/usr/bin/git config --local --get-all includeif.gitdir:/github/workspace/.git/worktrees/*.path
2026-11-07T07:18:48.2722182Z /github/runner_temp/git-credentials-588b07d4-b78a-4d0e-857f-b41935bac8a6.config
2026-11-07T07:18:48.2734552Z [command]/usr/bin/git config --local --unset includeif.gitdir:/github/workspace/.git/worktrees/*.path /github/runner_temp/git-credentials-588b07d4-b78a-4d0e-857f-b41935bac8a6.config
2026-11-07T07:18:48.2789588Z [command]/usr/bin/git submodule foreach --recursive git config --local --show-origin --name-only --get-regexp remote.origin.url
2026-11-07T07:18:48.3056679Z Removing credentials config '/home/runner/work/_temp/git-credentials-588b07d4-b78a-4d0e-857f-b41935bac8a6.config'
2026-11-07T07:18:48.3230203Z Cleaning up orphan processes

````
