# File-root regression fix — 7 November 2026

Tested checkpoint: `8104d8e8b1819765addab4fde3854fd37ccd81b2`.
[Focused CI #42360810124](https://github.com/eristavi/eristavi-lang/actions/runs/42360810124): **3/3 PASS**.
File probe 1/1 (13.206 s); generator parity 2/2 (255.978 s), with individual owned generators 98.233 / 98.333 s under unchanged 120 s limits.

The test incorrectly handed off the surviving outer File at byte offset 24 instead of canonical offset 32. It now exports actual fixture ValueId offsets/close IDs, reserves a complete 256-word SSA frame separately from roots/locals, and checks that an omitted handoff still faults. Correct nested close, forced GC and reclamation pass. No compiler/runtime or timeout change. This remains helper validation, not full Function File integration or U2 qualification.

The broader [smoke rerun #42360813812](https://github.com/eristavi/eristavi-lang/actions/runs/42360813812) was still running when this checkpoint was recorded. Do not call it passed. Logs below normalize trailing whitespace only.

## File roots

````text
﻿2026-11-07T09:41:49.1644195Z Current runner version: '2.338.2'
2026-11-07T09:41:49.1672128Z ##[group]Runner Image Provisioner
2026-11-07T09:41:49.1673087Z Hosted Compute Agent
2026-11-07T09:41:49.1673872Z Version: 20261028.624
2026-11-07T09:41:49.1674709Z Commit: 54898b74c23fde5556c9b3c3a2290865feef0dfe
2026-11-07T09:41:49.1675603Z Build Date: 2026-10-28T21:51:42Z
2026-11-07T09:41:49.1676517Z Worker ID: {a2b1e68f-16a7-44da-8a56-62eb68308ed7}
2026-11-07T09:41:49.1677565Z Region: centralus
2026-11-07T09:41:49.1678284Z Cloud: Azure
2026-11-07T09:41:49.1679005Z ##[endgroup]
2026-11-07T09:41:49.1680818Z ##[group]Operating System
2026-11-07T09:41:49.1681826Z Ubuntu
2026-11-07T09:41:49.1682525Z 24.04.5
2026-11-07T09:41:49.1683206Z LTS
2026-11-07T09:41:49.1683893Z ##[endgroup]
2026-11-07T09:41:49.1684686Z ##[group]Runner Image
2026-11-07T09:41:49.1685442Z Image: ubuntu-24.04
2026-11-07T09:41:49.1686263Z Version: 20261101.360.1
2026-11-07T09:41:49.1687875Z Included Software: https://github.com/actions/runner-images/blob/ubuntu24/20261101.360/images/ubuntu/Ubuntu2404-Readme.md
2026-11-07T09:41:49.1690566Z Image Release: https://github.com/actions/runner-images/releases/tag/ubuntu24%2F20261101.360
2026-11-07T09:41:49.1692014Z ##[endgroup]
2026-11-07T09:41:49.1693586Z ##[group]GITHUB_TOKEN Permissions
2026-11-07T09:41:49.1696361Z Contents: read
2026-11-07T09:41:49.1697183Z Metadata: read
2026-11-07T09:41:49.1697908Z ##[endgroup]
2026-11-07T09:41:49.1700130Z Secret source: Actions
2026-11-07T09:41:49.1701602Z Cache mode: write
2026-11-07T09:41:49.1702640Z Prepare workflow directory
2026-11-07T09:41:49.2019237Z Prepare all required actions
2026-11-07T09:41:49.2073520Z Getting action download info
2026-11-07T09:41:49.4385692Z Download action repository 'actions/checkout@v6' (SHA:d23441a48e516b6c34aea4fa41551a30e30af803)
2026-11-07T09:41:49.6713719Z Download action repository 'actions/setup-python@v6' (SHA:ece7cb06caefa5fff74198d8649806c4678c61a1)
2026-11-07T09:41:49.9868167Z Download action repository 'actions/upload-artifact@v6' (SHA:b7c566a772e6b6bfb58ed0dc250532a479d7789f)
2026-11-07T09:41:51.2105573Z Complete job name: File owner roots
2026-11-07T09:41:51.2760761Z ##[group]Run actions/checkout@v6
2026-11-07T09:41:51.2761494Z with:
2026-11-07T09:41:51.2761803Z   repository: eristavi/eristavi-lang
2026-11-07T09:41:51.2763983Z   token: ***
2026-11-07T09:41:51.2764291Z   ssh-strict: true
2026-11-07T09:41:51.2764581Z   ssh-user: git
2026-11-07T09:41:51.2764881Z   persist-credentials: true
2026-11-07T09:41:51.2765194Z   clean: true
2026-11-07T09:41:51.2765491Z   sparse-checkout-cone-mode: true
2026-11-07T09:41:51.2765811Z   fetch-depth: 1
2026-11-07T09:41:51.2766101Z   fetch-tags: false
2026-11-07T09:41:51.2766398Z   show-progress: true
2026-11-07T09:41:51.2766695Z   lfs: false
2026-11-07T09:41:51.2766977Z   submodules: false
2026-11-07T09:41:51.2767265Z   set-safe-directory: true
2026-11-07T09:41:51.2767582Z   allow-unsafe-pr-checkout: false
2026-11-07T09:41:51.2768052Z env:
2026-11-07T09:41:51.2768324Z   CC: clang
2026-11-07T09:41:51.2768638Z   CFLAGS: -O2
2026-11-07T09:41:51.2768946Z ##[endgroup]
2026-11-07T09:41:51.4708740Z Syncing repository: eristavi/eristavi-lang
2026-11-07T09:41:51.4710569Z ##[group]Getting Git version info
2026-11-07T09:41:51.4711381Z Working directory is '/home/runner/work/eristavi-lang/eristavi-lang'
2026-11-07T09:41:51.4712102Z [command]/usr/bin/git version
2026-11-07T09:41:51.4762038Z git version 2.56.0
2026-11-07T09:41:51.4777747Z ##[endgroup]
2026-11-07T09:41:51.4790763Z Temporarily overriding HOME='/home/runner/work/_temp/18121337-7b6a-49f0-af08-39a5f4002e99' before making global git config changes
2026-11-07T09:41:51.4792156Z Adding repository directory to the temporary git global config as a safe directory
2026-11-07T09:41:51.4795854Z [command]/usr/bin/git config --global --add safe.directory /home/runner/work/eristavi-lang/eristavi-lang
2026-11-07T09:41:51.4841489Z Deleting the contents of '/home/runner/work/eristavi-lang/eristavi-lang'
2026-11-07T09:41:51.4845647Z ##[group]Determining repository object format
2026-11-07T09:41:51.4847331Z ##[endgroup]
2026-11-07T09:41:51.4847849Z ##[group]Initializing the repository
2026-11-07T09:41:51.4851857Z [command]/usr/bin/git init /home/runner/work/eristavi-lang/eristavi-lang
2026-11-07T09:41:51.5255576Z hint: Using 'master' as the name for the initial branch. This default branch name
2026-11-07T09:41:51.5256701Z hint: will change to "main" in Git 3.0. To configure the initial branch name
2026-11-07T09:41:51.5257514Z hint: to use in all of your new repositories, which will suppress this warning,
2026-11-07T09:41:51.5258172Z hint: call:
2026-11-07T09:41:51.5258567Z hint:
2026-11-07T09:41:51.5259135Z hint: 	git config --global init.defaultBranch <name>
2026-11-07T09:41:51.5259695Z hint:
2026-11-07T09:41:51.5260222Z hint: Names commonly chosen instead of 'master' are 'main', 'trunk' and
2026-11-07T09:41:51.5261173Z hint: 'development'. The just-created branch can be renamed via this command:
2026-11-07T09:41:51.5261824Z hint:
2026-11-07T09:41:51.5262233Z hint: 	git branch -m <name>
2026-11-07T09:41:51.5262743Z hint:
2026-11-07T09:41:51.5263321Z hint: Disable this message with "git config set advice.defaultBranchName false"
2026-11-07T09:41:51.5264220Z Initialized empty Git repository in /home/runner/work/eristavi-lang/eristavi-lang/.git/
2026-11-07T09:41:51.5406442Z [command]/usr/bin/git remote add origin https://github.com/eristavi/eristavi-lang
2026-11-07T09:41:51.5408718Z ##[endgroup]
2026-11-07T09:41:51.5409552Z ##[group]Disabling automatic garbage collection
2026-11-07T09:41:51.5411261Z [command]/usr/bin/git config --local gc.auto 0
2026-11-07T09:41:51.5451538Z ##[endgroup]
2026-11-07T09:41:51.5452636Z ##[group]Setting up auth
2026-11-07T09:41:51.5453027Z Removing SSH command configuration
2026-11-07T09:41:51.5458331Z [command]/usr/bin/git config --local --name-only --get-regexp core\.sshCommand
2026-11-07T09:41:51.5497199Z [command]/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'core\.sshCommand' && git config --local --unset-all 'core.sshCommand' || :"
2026-11-07T09:41:51.5780495Z Removing HTTP extra header
2026-11-07T09:41:51.5786755Z [command]/usr/bin/git config --local --name-only --get-regexp http\.https\:\/\/github\.com\/\.extraheader
2026-11-07T09:41:51.5826289Z [command]/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'http\.https\:\/\/github\.com\/\.extraheader' && git config --local --unset-all 'http.https://github.com/.extraheader' || :"
2026-11-07T09:41:51.6038921Z Removing includeIf entries pointing to credentials config files
2026-11-07T09:41:51.6039650Z [command]/usr/bin/git config --local --name-only --get-regexp ^includeIf\.gitdir:
2026-11-07T09:41:51.6077099Z [command]/usr/bin/git submodule foreach --recursive git config --local --show-origin --name-only --get-regexp remote.origin.url
2026-11-07T09:41:51.6285725Z [command]/usr/bin/git config --file /home/runner/work/_temp/git-credentials-48292c69-b954-4838-80d3-196f21e4e467.config http.https://github.com/.extraheader AUTHORIZATION: basic ***
2026-11-07T09:41:51.6327754Z [command]/usr/bin/git config --local includeIf.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git.path /home/runner/work/_temp/git-credentials-48292c69-b954-4838-80d3-196f21e4e467.config
2026-11-07T09:41:51.6363546Z [command]/usr/bin/git config --local includeIf.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git/worktrees/*.path /home/runner/work/_temp/git-credentials-48292c69-b954-4838-80d3-196f21e4e467.config
2026-11-07T09:41:51.6400566Z [command]/usr/bin/git config --local includeIf.gitdir:/github/workspace/.git.path /github/runner_temp/git-credentials-48292c69-b954-4838-80d3-196f21e4e467.config
2026-11-07T09:41:51.7307198Z [command]/usr/bin/git config --local includeIf.gitdir:/github/workspace/.git/worktrees/*.path /github/runner_temp/git-credentials-48292c69-b954-4838-80d3-196f21e4e467.config
2026-11-07T09:41:51.7343314Z ##[endgroup]
2026-11-07T09:41:51.7343807Z ##[group]Fetching the repository
2026-11-07T09:41:51.7351740Z [command]/usr/bin/git -c protocol.version=2 fetch --no-tags --prune --no-recurse-submodules --depth=1 origin +8104d8e8b1819765addab4fde3854fd37ccd81b2:refs/remotes/origin/compiler/u2-whole-function-file-roots-20261107
2026-11-07T09:41:52.4813618Z From https://github.com/eristavi/eristavi-lang
2026-11-07T09:41:52.4814289Z  * [new ref]         8104d8e8b1819765addab4fde3854fd37ccd81b2 -> origin/compiler/u2-whole-function-file-roots-20261107
2026-11-07T09:41:52.4823078Z [command]/usr/bin/git branch --list --remote origin/compiler/u2-whole-function-file-roots-20261107
2026-11-07T09:41:52.4852442Z   origin/compiler/u2-whole-function-file-roots-20261107
2026-11-07T09:41:52.4859174Z [command]/usr/bin/git rev-parse refs/remotes/origin/compiler/u2-whole-function-file-roots-20261107
2026-11-07T09:41:52.4886494Z 8104d8e8b1819765addab4fde3854fd37ccd81b2
2026-11-07T09:41:52.4890574Z ##[endgroup]
2026-11-07T09:41:52.4891207Z ##[group]Determining the checkout info
2026-11-07T09:41:52.4891703Z ##[endgroup]
2026-11-07T09:41:52.4895485Z [command]/usr/bin/git sparse-checkout disable
2026-11-07T09:41:52.4943590Z [command]/usr/bin/git config --local --unset-all extensions.worktreeConfig
2026-11-07T09:41:52.4975868Z ##[group]Checking out the ref
2026-11-07T09:41:52.4979047Z [command]/usr/bin/git checkout --progress --force -B compiler/u2-whole-function-file-roots-20261107 refs/remotes/origin/compiler/u2-whole-function-file-roots-20261107
2026-11-07T09:41:52.5680681Z Switched to a new branch 'compiler/u2-whole-function-file-roots-20261107'
2026-11-07T09:41:52.5688195Z branch 'compiler/u2-whole-function-file-roots-20261107' set up to track 'origin/compiler/u2-whole-function-file-roots-20261107'.
2026-11-07T09:41:52.5691478Z ##[endgroup]
2026-11-07T09:41:52.5735571Z [command]/usr/bin/git log -1 --format=%H
2026-11-07T09:41:52.5764815Z 8104d8e8b1819765addab4fde3854fd37ccd81b2
2026-11-07T09:41:52.5989765Z ##[group]Run actions/setup-python@v6
2026-11-07T09:41:52.5990031Z with:
2026-11-07T09:41:52.6055479Z   python-version: 3.11
2026-11-07T09:41:52.6055731Z   check-latest: false
2026-11-07T09:41:52.6057849Z   token: ***
2026-11-07T09:41:52.6058076Z   update-environment: true
2026-11-07T09:41:52.6058317Z   allow-prereleases: false
2026-11-07T09:41:52.6058556Z   freethreaded: false
2026-11-07T09:41:52.6058767Z env:
2026-11-07T09:41:52.6058962Z   CC: clang
2026-11-07T09:41:52.6059149Z   CFLAGS: -O2
2026-11-07T09:41:52.6059340Z ##[endgroup]
2026-11-07T09:41:52.7155089Z ##[group]Installed versions
2026-11-07T09:41:52.7226991Z Successfully set up CPython (3.11.18)
2026-11-07T09:41:52.7227680Z ##[endgroup]
2026-11-07T09:41:52.7380754Z ##[group]Run python -m pip install -e .
2026-11-07T09:41:52.7381459Z [36;1mpython -m pip install -e .[0m
2026-11-07T09:41:52.7416992Z shell: /usr/bin/bash -e {0}
2026-11-07T09:41:52.7417365Z env:
2026-11-07T09:41:52.7417648Z   CC: clang
2026-11-07T09:41:52.7417946Z   CFLAGS: -O2
2026-11-07T09:41:52.7418340Z   pythonLocation: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T09:41:52.7418967Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib/pkgconfig
2026-11-07T09:41:52.7419608Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T09:41:52.7420156Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T09:41:52.7420692Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T09:41:52.7421334Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib
2026-11-07T09:41:52.7421783Z ##[endgroup]
2026-11-07T09:41:53.3649865Z Obtaining file:///home/runner/work/eristavi-lang/eristavi-lang
2026-11-07T09:41:53.3661944Z   Installing build dependencies: started
2026-11-07T09:41:54.0328313Z   Installing build dependencies: finished with status 'done'
2026-11-07T09:41:54.0332247Z   Checking if build backend supports build_editable: started
2026-11-07T09:41:54.4567831Z   Checking if build backend supports build_editable: finished with status 'done'
2026-11-07T09:41:54.4573406Z   Getting requirements to build editable: started
2026-11-07T09:41:54.7680247Z   Getting requirements to build editable: finished with status 'done'
2026-11-07T09:41:54.7687646Z   Preparing editable metadata (pyproject.toml): started
2026-11-07T09:41:54.9107826Z   Preparing editable metadata (pyproject.toml): finished with status 'done'
2026-11-07T09:41:55.2871274Z Collecting regex==2026.9.29 (from eristavi-lang==0.0.1.dev0)
2026-11-07T09:41:55.3611218Z   Downloading regex-2026.9.29-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (40 kB)
2026-11-07T09:41:55.5191843Z Collecting unicodedata2==17.0.0 (from eristavi-lang==0.0.1.dev0)
2026-11-07T09:41:55.5358475Z   Downloading unicodedata2-17.0.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (3.3 kB)
2026-11-07T09:41:55.5653022Z Downloading regex-2026.9.29-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (804 kB)
2026-11-07T09:41:55.7678323Z    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 805.0/805.0 kB 3.1 MB/s  0:00:00
2026-11-07T09:41:55.7859309Z Downloading unicodedata2-17.0.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (531 kB)
2026-11-07T09:41:55.8233610Z    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 531.5/531.5 kB 7.8 MB/s  0:00:00
2026-11-07T09:41:55.8305049Z Building wheels for collected packages: eristavi-lang
2026-11-07T09:41:55.8311747Z   Building editable for eristavi-lang (pyproject.toml): started
2026-11-07T09:41:56.9029527Z   Building editable for eristavi-lang (pyproject.toml): finished with status 'done'
2026-11-07T09:41:56.9034043Z   Created wheel for eristavi-lang: filename=eristavi_lang-0.0.1.dev0-0.editable-py3-none-any.whl size=4073 sha256=474fd64b6ab0d44d4c892256046a24722801382558c0d6991049866e1ef236a2
2026-11-07T09:41:56.9035521Z   Stored in directory: /tmp/pip-ephem-wheel-cache-u8zk00ja/wheels/bf/0e/13/3c92c3d16e7da71040fe0218774d6a7875df473d79c0e7b5aa
2026-11-07T09:41:56.9051725Z Successfully built eristavi-lang
2026-11-07T09:41:56.9176271Z Installing collected packages: unicodedata2, regex, eristavi-lang
2026-11-07T09:41:58.4354388Z
2026-11-07T09:41:58.4361655Z Successfully installed eristavi-lang-0.0.1.dev0 regex-2026.9.29 unicodedata2-17.0.0
2026-11-07T09:41:58.4367827Z
2026-11-07T09:41:58.4368140Z [notice] A new release of pip is available: 26.2.2 -> 26.3
2026-11-07T09:41:58.4368609Z [notice] To update, run: pip install --upgrade pip
2026-11-07T09:41:58.5153513Z ##[group]Run set -o pipefail
2026-11-07T09:41:58.5153825Z [36;1mset -o pipefail[0m
2026-11-07T09:41:58.5154237Z [36;1mPYTHONPATH=tests:. python -u -m unittest -v test_u2_function_file_roots 2>&1 | tee "$RUNNER_TEMP/focused.log"[0m
2026-11-07T09:41:58.5173914Z shell: /usr/bin/bash --noprofile --norc -e -o pipefail {0}
2026-11-07T09:41:58.5174195Z env:
2026-11-07T09:41:58.5174361Z   CC: clang
2026-11-07T09:41:58.5174524Z   CFLAGS: -O2
2026-11-07T09:41:58.5174746Z   pythonLocation: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T09:41:58.5175083Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib/pkgconfig
2026-11-07T09:41:58.5175416Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T09:41:58.5175728Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T09:41:58.5176032Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T09:41:58.5176338Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib
2026-11-07T09:41:58.5176639Z ##[endgroup]
2026-11-07T09:42:12.1966514Z test_verified_lexical_owner_roots_cover_every_original_block_and_consumption (test_u2_function_file_roots.U2WholeFunctionFileRootTests.test_verified_lexical_owner_roots_cover_every_original_block_and_consumption) ... ok
2026-11-07T09:42:12.1969422Z
2026-11-07T09:42:12.1969659Z ----------------------------------------------------------------------
2026-11-07T09:42:12.1970245Z Ran 1 test in 13.206s
2026-11-07T09:42:12.1970482Z
2026-11-07T09:42:12.1970694Z OK
2026-11-07T09:42:12.2584486Z ##[group]Run actions/upload-artifact@v6
2026-11-07T09:42:12.2584732Z with:
2026-11-07T09:42:12.2584905Z   name: u2-file-root-fix-0
2026-11-07T09:42:12.2585119Z   path: /home/runner/work/_temp/focused.log
2026-11-07T09:42:12.2585493Z   retention-days: 14
2026-11-07T09:42:12.2585694Z   if-no-files-found: warn
2026-11-07T09:42:12.2585892Z   compression-level: 6
2026-11-07T09:42:12.2586072Z   overwrite: false
2026-11-07T09:42:12.2586245Z   include-hidden-files: false
2026-11-07T09:42:12.2586434Z env:
2026-11-07T09:42:12.2586584Z   CC: clang
2026-11-07T09:42:12.2586741Z   CFLAGS: -O2
2026-11-07T09:42:12.2586947Z   pythonLocation: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T09:42:12.2587280Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib/pkgconfig
2026-11-07T09:42:12.2587619Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T09:42:12.2587919Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T09:42:12.2588253Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T09:42:12.2588549Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib
2026-11-07T09:42:12.2588799Z ##[endgroup]
2026-11-07T09:42:12.3842082Z With the provided path, there will be 1 file uploaded
2026-11-07T09:42:12.3846172Z Artifact name is valid!
2026-11-07T09:42:12.3846815Z Root directory input is valid!
2026-11-07T09:42:12.6502909Z Beginning upload of artifact content to blob storage
2026-11-07T09:42:12.7855386Z Uploaded bytes 284
2026-11-07T09:42:12.8186252Z Finished uploading artifact content to blob storage!
2026-11-07T09:42:12.8189606Z SHA256 digest of uploaded artifact zip is 63ca4f38e3cff505a30d85eba6ac3717b14168166c1a0a5db88e2bc5b40e6a87
2026-11-07T09:42:12.8190307Z Finalizing artifact upload
2026-11-07T09:42:13.2799857Z Artifact u2-file-root-fix-0.zip successfully finalized. Artifact ID 13569478299
2026-11-07T09:42:13.2800726Z Artifact u2-file-root-fix-0 has been successfully uploaded! Final size is 284 bytes. Artifact ID is 13569478299
2026-11-07T09:42:13.2805397Z Artifact download URL: https://github.com/eristavi/eristavi-lang/actions/runs/42360810124/artifacts/13569478299
2026-11-07T09:42:13.2981810Z Post job cleanup.
2026-11-07T09:42:13.4176667Z Post job cleanup.
2026-11-07T09:42:13.4909674Z [command]/usr/bin/git version
2026-11-07T09:42:13.4951385Z git version 2.56.0
2026-11-07T09:42:13.5024001Z Temporarily overriding HOME='/home/runner/work/_temp/2de5adae-13ff-41eb-86ea-136ee9f69865' before making global git config changes
2026-11-07T09:42:13.5025163Z Adding repository directory to the temporary git global config as a safe directory
2026-11-07T09:42:13.5029876Z [command]/usr/bin/git config --global --add safe.directory /home/runner/work/eristavi-lang/eristavi-lang
2026-11-07T09:42:13.5071390Z Removing SSH command configuration
2026-11-07T09:42:13.5079116Z [command]/usr/bin/git config --local --name-only --get-regexp core\.sshCommand
2026-11-07T09:42:13.5119059Z [command]/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'core\.sshCommand' && git config --local --unset-all 'core.sshCommand' || :"
2026-11-07T09:42:13.5422927Z Removing HTTP extra header
2026-11-07T09:42:13.5423845Z [command]/usr/bin/git config --local --name-only --get-regexp http\.https\:\/\/github\.com\/\.extraheader
2026-11-07T09:42:13.5473454Z [command]/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'http\.https\:\/\/github\.com\/\.extraheader' && git config --local --unset-all 'http.https://github.com/.extraheader' || :"
2026-11-07T09:42:13.5813381Z Removing includeIf entries pointing to credentials config files
2026-11-07T09:42:13.5814454Z [command]/usr/bin/git config --local --name-only --get-regexp ^includeIf\.gitdir:
2026-11-07T09:42:13.5845900Z includeif.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git.path
2026-11-07T09:42:13.5846715Z includeif.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git/worktrees/*.path
2026-11-07T09:42:13.5847370Z includeif.gitdir:/github/workspace/.git.path
2026-11-07T09:42:13.5847876Z includeif.gitdir:/github/workspace/.git/worktrees/*.path
2026-11-07T09:42:13.5850791Z [command]/usr/bin/git config --local --get-all includeif.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git.path
2026-11-07T09:42:13.5882730Z /home/runner/work/_temp/git-credentials-48292c69-b954-4838-80d3-196f21e4e467.config
2026-11-07T09:42:13.5892155Z [command]/usr/bin/git config --local --unset includeif.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git.path /home/runner/work/_temp/git-credentials-48292c69-b954-4838-80d3-196f21e4e467.config
2026-11-07T09:42:13.5932693Z [command]/usr/bin/git config --local --get-all includeif.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git/worktrees/*.path
2026-11-07T09:42:13.5963853Z /home/runner/work/_temp/git-credentials-48292c69-b954-4838-80d3-196f21e4e467.config
2026-11-07T09:42:13.5971696Z [command]/usr/bin/git config --local --unset includeif.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git/worktrees/*.path /home/runner/work/_temp/git-credentials-48292c69-b954-4838-80d3-196f21e4e467.config
2026-11-07T09:42:13.6008783Z [command]/usr/bin/git config --local --get-all includeif.gitdir:/github/workspace/.git.path
2026-11-07T09:42:13.6038866Z /github/runner_temp/git-credentials-48292c69-b954-4838-80d3-196f21e4e467.config
2026-11-07T09:42:13.6045286Z [command]/usr/bin/git config --local --unset includeif.gitdir:/github/workspace/.git.path /github/runner_temp/git-credentials-48292c69-b954-4838-80d3-196f21e4e467.config
2026-11-07T09:42:13.6083713Z [command]/usr/bin/git config --local --get-all includeif.gitdir:/github/workspace/.git/worktrees/*.path
2026-11-07T09:42:13.6112115Z /github/runner_temp/git-credentials-48292c69-b954-4838-80d3-196f21e4e467.config
2026-11-07T09:42:13.6118048Z [command]/usr/bin/git config --local --unset includeif.gitdir:/github/workspace/.git/worktrees/*.path /github/runner_temp/git-credentials-48292c69-b954-4838-80d3-196f21e4e467.config
2026-11-07T09:42:13.6161733Z [command]/usr/bin/git submodule foreach --recursive git config --local --show-origin --name-only --get-regexp remote.origin.url
2026-11-07T09:42:13.6376704Z Removing credentials config '/home/runner/work/_temp/git-credentials-48292c69-b954-4838-80d3-196f21e4e467.config'
2026-11-07T09:42:13.6511126Z Cleaning up orphan processes

````

## Generator parity

````text
﻿2026-11-07T09:41:49.6110865Z Current runner version: '2.338.2'
2026-11-07T09:41:49.6133043Z ##[group]Runner Image Provisioner
2026-11-07T09:41:49.6133864Z Hosted Compute Agent
2026-11-07T09:41:49.6134379Z Version: 20261028.624
2026-11-07T09:41:49.6134986Z Commit: 54898b74c23fde5556c9b3c3a2290865feef0dfe
2026-11-07T09:41:49.6135649Z Build Date: 2026-10-28T21:51:42Z
2026-11-07T09:41:49.6136616Z Worker ID: {9fc2fdf5-15e9-4450-ac78-31355d9a9e76}
2026-11-07T09:41:49.6137273Z Region: westus3
2026-11-07T09:41:49.6137754Z Cloud: Azure
2026-11-07T09:41:49.6138208Z ##[endgroup]
2026-11-07T09:41:49.6139485Z ##[group]Operating System
2026-11-07T09:41:49.6140023Z Ubuntu
2026-11-07T09:41:49.6140521Z 24.04.5
2026-11-07T09:41:49.6140990Z LTS
2026-11-07T09:41:49.6141446Z ##[endgroup]
2026-11-07T09:41:49.6142025Z ##[group]Runner Image
2026-11-07T09:41:49.6142537Z Image: ubuntu-24.04
2026-11-07T09:41:49.6143052Z Version: 20261101.360.1
2026-11-07T09:41:49.6144174Z Included Software: https://github.com/actions/runner-images/blob/ubuntu24/20261101.360/images/ubuntu/Ubuntu2404-Readme.md
2026-11-07T09:41:49.6146178Z Image Release: https://github.com/actions/runner-images/releases/tag/ubuntu24%2F20261101.360
2026-11-07T09:41:49.6147018Z ##[endgroup]
2026-11-07T09:41:49.6148011Z ##[group]GITHUB_TOKEN Permissions
2026-11-07T09:41:49.6149713Z Contents: read
2026-11-07T09:41:49.6150316Z Metadata: read
2026-11-07T09:41:49.6150816Z ##[endgroup]
2026-11-07T09:41:49.6152970Z Secret source: Actions
2026-11-07T09:41:49.6153844Z Cache mode: write
2026-11-07T09:41:49.6154634Z Prepare workflow directory
2026-11-07T09:41:49.6491773Z Prepare all required actions
2026-11-07T09:41:49.6533142Z Getting action download info
2026-11-07T09:41:49.9345402Z Download action repository 'actions/checkout@v6' (SHA:d23441a48e516b6c34aea4fa41551a30e30af803)
2026-11-07T09:41:50.0265015Z Download action repository 'actions/setup-python@v6' (SHA:ece7cb06caefa5fff74198d8649806c4678c61a1)
2026-11-07T09:41:50.1269163Z Download action repository 'actions/upload-artifact@v6' (SHA:b7c566a772e6b6bfb58ed0dc250532a479d7789f)
2026-11-07T09:41:50.3609968Z Complete job name: Generator parity watchdogs
2026-11-07T09:41:50.4364040Z ##[group]Run actions/checkout@v6
2026-11-07T09:41:50.4364743Z with:
2026-11-07T09:41:50.4365113Z   repository: eristavi/eristavi-lang
2026-11-07T09:41:50.4368647Z   token: ***
2026-11-07T09:41:50.4369016Z   ssh-strict: true
2026-11-07T09:41:50.4369385Z   ssh-user: git
2026-11-07T09:41:50.4369755Z   persist-credentials: true
2026-11-07T09:41:50.4370146Z   clean: true
2026-11-07T09:41:50.4370508Z   sparse-checkout-cone-mode: true
2026-11-07T09:41:50.4370918Z   fetch-depth: 1
2026-11-07T09:41:50.4371260Z   fetch-tags: false
2026-11-07T09:41:50.4371614Z   show-progress: true
2026-11-07T09:41:50.4371972Z   lfs: false
2026-11-07T09:41:50.4372306Z   submodules: false
2026-11-07T09:41:50.4372664Z   set-safe-directory: true
2026-11-07T09:41:50.4373062Z   allow-unsafe-pr-checkout: false
2026-11-07T09:41:50.4373662Z env:
2026-11-07T09:41:50.4373980Z   CC: clang
2026-11-07T09:41:50.4374347Z   CFLAGS: -O2
2026-11-07T09:41:50.4374719Z ##[endgroup]
2026-11-07T09:41:50.6541836Z Syncing repository: eristavi/eristavi-lang
2026-11-07T09:41:50.6543549Z ##[group]Getting Git version info
2026-11-07T09:41:50.6544430Z Working directory is '/home/runner/work/eristavi-lang/eristavi-lang'
2026-11-07T09:41:50.6545668Z [command]/usr/bin/git version
2026-11-07T09:41:50.6608553Z git version 2.56.0
2026-11-07T09:41:50.6635256Z ##[endgroup]
2026-11-07T09:41:50.6653697Z Temporarily overriding HOME='/home/runner/work/_temp/92f39e3b-4d5e-4be3-a0c9-bd9dac9d0b4d' before making global git config changes
2026-11-07T09:41:50.6655701Z Adding repository directory to the temporary git global config as a safe directory
2026-11-07T09:41:50.6659932Z [command]/usr/bin/git config --global --add safe.directory /home/runner/work/eristavi-lang/eristavi-lang
2026-11-07T09:41:50.6721217Z Deleting the contents of '/home/runner/work/eristavi-lang/eristavi-lang'
2026-11-07T09:41:50.6726990Z ##[group]Determining repository object format
2026-11-07T09:41:50.6729502Z ##[endgroup]
2026-11-07T09:41:50.6730556Z ##[group]Initializing the repository
2026-11-07T09:41:50.6736254Z [command]/usr/bin/git init /home/runner/work/eristavi-lang/eristavi-lang
2026-11-07T09:41:50.6835571Z hint: Using 'master' as the name for the initial branch. This default branch name
2026-11-07T09:41:50.6837421Z hint: will change to "main" in Git 3.0. To configure the initial branch name
2026-11-07T09:41:50.6838751Z hint: to use in all of your new repositories, which will suppress this warning,
2026-11-07T09:41:50.6839826Z hint: call:
2026-11-07T09:41:50.6840457Z hint:
2026-11-07T09:41:50.6841186Z hint: 	git config --global init.defaultBranch <name>
2026-11-07T09:41:50.6842097Z hint:
2026-11-07T09:41:50.6842888Z hint: Names commonly chosen instead of 'master' are 'main', 'trunk' and
2026-11-07T09:41:50.6844149Z hint: 'development'. The just-created branch can be renamed via this command:
2026-11-07T09:41:50.6846169Z hint:
2026-11-07T09:41:50.6847570Z hint: 	git branch -m <name>
2026-11-07T09:41:50.6848300Z hint:
2026-11-07T09:41:50.6849172Z hint: Disable this message with "git config set advice.defaultBranchName false"
2026-11-07T09:41:50.6850764Z Initialized empty Git repository in /home/runner/work/eristavi-lang/eristavi-lang/.git/
2026-11-07T09:41:50.6855244Z [command]/usr/bin/git remote add origin https://github.com/eristavi/eristavi-lang
2026-11-07T09:41:50.6911022Z ##[endgroup]
2026-11-07T09:41:50.6912160Z ##[group]Disabling automatic garbage collection
2026-11-07T09:41:50.6916453Z [command]/usr/bin/git config --local gc.auto 0
2026-11-07T09:41:50.6964546Z ##[endgroup]
2026-11-07T09:41:50.6966096Z ##[group]Setting up auth
2026-11-07T09:41:50.6966996Z Removing SSH command configuration
2026-11-07T09:41:50.6972936Z [command]/usr/bin/git config --local --name-only --get-regexp core\.sshCommand
2026-11-07T09:41:50.7021991Z [command]/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'core\.sshCommand' && git config --local --unset-all 'core.sshCommand' || :"
2026-11-07T09:41:50.7390525Z Removing HTTP extra header
2026-11-07T09:41:50.7392070Z [command]/usr/bin/git config --local --name-only --get-regexp http\.https\:\/\/github\.com\/\.extraheader
2026-11-07T09:41:50.7441759Z [command]/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'http\.https\:\/\/github\.com\/\.extraheader' && git config --local --unset-all 'http.https://github.com/.extraheader' || :"
2026-11-07T09:41:50.7654405Z Removing includeIf entries pointing to credentials config files
2026-11-07T09:41:50.7660111Z [command]/usr/bin/git config --local --name-only --get-regexp ^includeIf\.gitdir:
2026-11-07T09:41:50.7706748Z [command]/usr/bin/git submodule foreach --recursive git config --local --show-origin --name-only --get-regexp remote.origin.url
2026-11-07T09:41:50.7929401Z [command]/usr/bin/git config --file /home/runner/work/_temp/git-credentials-3ddfc5bd-1c83-46db-977c-5d0405790193.config http.https://github.com/.extraheader AUTHORIZATION: basic ***
2026-11-07T09:41:50.7974798Z [command]/usr/bin/git config --local includeIf.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git.path /home/runner/work/_temp/git-credentials-3ddfc5bd-1c83-46db-977c-5d0405790193.config
2026-11-07T09:41:50.8015014Z [command]/usr/bin/git config --local includeIf.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git/worktrees/*.path /home/runner/work/_temp/git-credentials-3ddfc5bd-1c83-46db-977c-5d0405790193.config
2026-11-07T09:41:50.8055314Z [command]/usr/bin/git config --local includeIf.gitdir:/github/workspace/.git.path /github/runner_temp/git-credentials-3ddfc5bd-1c83-46db-977c-5d0405790193.config
2026-11-07T09:41:50.8102175Z [command]/usr/bin/git config --local includeIf.gitdir:/github/workspace/.git/worktrees/*.path /github/runner_temp/git-credentials-3ddfc5bd-1c83-46db-977c-5d0405790193.config
2026-11-07T09:41:50.8347988Z ##[endgroup]
2026-11-07T09:41:50.8348670Z ##[group]Fetching the repository
2026-11-07T09:41:50.8356243Z [command]/usr/bin/git -c protocol.version=2 fetch --no-tags --prune --no-recurse-submodules --depth=1 origin +8104d8e8b1819765addab4fde3854fd37ccd81b2:refs/remotes/origin/compiler/u2-whole-function-file-roots-20261107
2026-11-07T09:41:51.8277107Z From https://github.com/eristavi/eristavi-lang
2026-11-07T09:41:51.8278935Z  * [new ref]         8104d8e8b1819765addab4fde3854fd37ccd81b2 -> origin/compiler/u2-whole-function-file-roots-20261107
2026-11-07T09:41:51.8286009Z [command]/usr/bin/git branch --list --remote origin/compiler/u2-whole-function-file-roots-20261107
2026-11-07T09:41:51.8321517Z   origin/compiler/u2-whole-function-file-roots-20261107
2026-11-07T09:41:51.8332002Z [command]/usr/bin/git rev-parse refs/remotes/origin/compiler/u2-whole-function-file-roots-20261107
2026-11-07T09:41:51.8367287Z 8104d8e8b1819765addab4fde3854fd37ccd81b2
2026-11-07T09:41:51.8378129Z ##[endgroup]
2026-11-07T09:41:51.8379099Z ##[group]Determining the checkout info
2026-11-07T09:41:51.8380143Z ##[endgroup]
2026-11-07T09:41:51.8380739Z [command]/usr/bin/git sparse-checkout disable
2026-11-07T09:41:51.8438333Z [command]/usr/bin/git config --local --unset-all extensions.worktreeConfig
2026-11-07T09:41:51.8477177Z ##[group]Checking out the ref
2026-11-07T09:41:51.8480969Z [command]/usr/bin/git checkout --progress --force -B compiler/u2-whole-function-file-roots-20261107 refs/remotes/origin/compiler/u2-whole-function-file-roots-20261107
2026-11-07T09:41:51.9197935Z Switched to a new branch 'compiler/u2-whole-function-file-roots-20261107'
2026-11-07T09:41:51.9207819Z branch 'compiler/u2-whole-function-file-roots-20261107' set up to track 'origin/compiler/u2-whole-function-file-roots-20261107'.
2026-11-07T09:41:51.9218716Z ##[endgroup]
2026-11-07T09:41:51.9264985Z [command]/usr/bin/git log -1 --format=%H
2026-11-07T09:41:51.9299232Z 8104d8e8b1819765addab4fde3854fd37ccd81b2
2026-11-07T09:41:51.9678008Z ##[group]Run actions/setup-python@v6
2026-11-07T09:41:51.9678712Z with:
2026-11-07T09:41:51.9679102Z   python-version: 3.11
2026-11-07T09:41:51.9679583Z   check-latest: false
2026-11-07T09:41:51.9687462Z   token: ***
2026-11-07T09:41:51.9687907Z   update-environment: true
2026-11-07T09:41:51.9688451Z   allow-prereleases: false
2026-11-07T09:41:51.9688995Z   freethreaded: false
2026-11-07T09:41:51.9689447Z env:
2026-11-07T09:41:51.9689799Z   CC: clang
2026-11-07T09:41:51.9690190Z   CFLAGS: -O2
2026-11-07T09:41:51.9690616Z ##[endgroup]
2026-11-07T09:41:52.0854495Z ##[group]Installed versions
2026-11-07T09:41:52.0934158Z Successfully set up CPython (3.11.18)
2026-11-07T09:41:52.0935692Z ##[endgroup]
2026-11-07T09:41:52.1133154Z ##[group]Run python -m pip install -e .
2026-11-07T09:41:52.1134040Z [36;1mpython -m pip install -e .[0m
2026-11-07T09:41:52.1172270Z shell: /usr/bin/bash -e {0}
2026-11-07T09:41:52.1172985Z env:
2026-11-07T09:41:52.1173377Z   CC: clang
2026-11-07T09:41:52.1173762Z   CFLAGS: -O2
2026-11-07T09:41:52.1174350Z   pythonLocation: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T09:41:52.1175601Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib/pkgconfig
2026-11-07T09:41:52.1178055Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T09:41:52.1179411Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T09:41:52.1180890Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T09:41:52.1182331Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib
2026-11-07T09:41:52.1183379Z ##[endgroup]
2026-11-07T09:41:52.8792150Z Obtaining file:///home/runner/work/eristavi-lang/eristavi-lang
2026-11-07T09:41:52.8804471Z   Installing build dependencies: started
2026-11-07T09:41:53.5693898Z   Installing build dependencies: finished with status 'done'
2026-11-07T09:41:53.5700007Z   Checking if build backend supports build_editable: started
2026-11-07T09:41:53.8346111Z   Checking if build backend supports build_editable: finished with status 'done'
2026-11-07T09:41:53.8352349Z   Getting requirements to build editable: started
2026-11-07T09:41:54.1117938Z   Getting requirements to build editable: finished with status 'done'
2026-11-07T09:41:54.1126731Z   Preparing editable metadata (pyproject.toml): started
2026-11-07T09:41:54.2734433Z   Preparing editable metadata (pyproject.toml): finished with status 'done'
2026-11-07T09:41:54.6757488Z Collecting regex==2026.9.29 (from eristavi-lang==0.0.1.dev0)
2026-11-07T09:41:54.7337367Z   Downloading regex-2026.9.29-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (40 kB)
2026-11-07T09:41:54.7868391Z Collecting unicodedata2==17.0.0 (from eristavi-lang==0.0.1.dev0)
2026-11-07T09:41:54.7981835Z   Downloading unicodedata2-17.0.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (3.3 kB)
2026-11-07T09:41:54.8183861Z Downloading regex-2026.9.29-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (804 kB)
2026-11-07T09:41:54.8974103Z    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 805.0/805.0 kB 11.0 MB/s  0:00:00
2026-11-07T09:41:54.9083357Z Downloading unicodedata2-17.0.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (531 kB)
2026-11-07T09:41:54.9475196Z    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 531.5/531.5 kB 13.7 MB/s  0:00:00
2026-11-07T09:41:54.9549555Z Building wheels for collected packages: eristavi-lang
2026-11-07T09:41:54.9557291Z   Building editable for eristavi-lang (pyproject.toml): started
2026-11-07T09:41:55.1304244Z   Building editable for eristavi-lang (pyproject.toml): finished with status 'done'
2026-11-07T09:41:55.1308702Z   Created wheel for eristavi-lang: filename=eristavi_lang-0.0.1.dev0-0.editable-py3-none-any.whl size=4073 sha256=42a844c1254d92d8afdbc678170c3c51fb9edae9ad97443b90de5b79c6f5deb5
2026-11-07T09:41:55.1310373Z   Stored in directory: /tmp/pip-ephem-wheel-cache-66f7wty8/wheels/bf/0e/13/3c92c3d16e7da71040fe0218774d6a7875df473d79c0e7b5aa
2026-11-07T09:41:55.1321800Z Successfully built eristavi-lang
2026-11-07T09:41:55.1458181Z Installing collected packages: unicodedata2, regex, eristavi-lang
2026-11-07T09:41:55.2820029Z
2026-11-07T09:41:55.2827609Z Successfully installed eristavi-lang-0.0.1.dev0 regex-2026.9.29 unicodedata2-17.0.0
2026-11-07T09:41:55.2834179Z
2026-11-07T09:41:55.2834590Z [notice] A new release of pip is available: 26.2.2 -> 26.3
2026-11-07T09:41:55.2835074Z [notice] To update, run: pip install --upgrade pip
2026-11-07T09:41:55.3804821Z ##[group]Run set -o pipefail
2026-11-07T09:41:55.3805148Z [36;1mset -o pipefail[0m
2026-11-07T09:41:55.3806277Z [36;1mPYTHONPATH=tests:. python -u -m unittest -v test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_owned_and_c_bootstrap_generators_emit_identical_checked_function test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_owned_and_c_generators_agree_on_direct_group 2>&1 | tee "$RUNNER_TEMP/focused.log"[0m
2026-11-07T09:41:55.3827814Z shell: /usr/bin/bash --noprofile --norc -e -o pipefail {0}
2026-11-07T09:41:55.3828107Z env:
2026-11-07T09:41:55.3828280Z   CC: clang
2026-11-07T09:41:55.3828447Z   CFLAGS: -O2
2026-11-07T09:41:55.3828677Z   pythonLocation: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T09:41:55.3829041Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib/pkgconfig
2026-11-07T09:41:55.3829377Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T09:41:55.3829745Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T09:41:55.3830060Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T09:41:55.3830363Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib
2026-11-07T09:41:55.3830632Z ##[endgroup]
2026-11-07T09:43:59.4549991Z test_owned_and_c_bootstrap_generators_emit_identical_checked_function (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_owned_and_c_bootstrap_generators_emit_identical_checked_function) ... U2_CHECKED_OWNED_GENERATOR_SECONDS=98.23305269400001
2026-11-07T09:44:04.7094490Z ok
2026-11-07T09:46:11.7032005Z test_owned_and_c_generators_agree_on_direct_group (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_owned_and_c_generators_agree_on_direct_group) ... U2_DIRECT_GROUP_OWNED_GENERATOR_SECONDS=98.333
2026-11-07T09:46:11.8086562Z ok
2026-11-07T09:46:11.8109969Z
2026-11-07T09:46:11.8110241Z ----------------------------------------------------------------------
2026-11-07T09:46:11.8110725Z Ran 2 tests in 255.978s
2026-11-07T09:46:11.8111020Z
2026-11-07T09:46:11.8112919Z OK
2026-11-07T09:46:11.8444292Z ##[group]Run actions/upload-artifact@v6
2026-11-07T09:46:11.8444542Z with:
2026-11-07T09:46:11.8444714Z   name: u2-file-root-fix-1
2026-11-07T09:46:11.8444931Z   path: /home/runner/work/_temp/focused.log
2026-11-07T09:46:11.8445167Z   retention-days: 14
2026-11-07T09:46:11.8445351Z   if-no-files-found: warn
2026-11-07T09:46:11.8445541Z   compression-level: 6
2026-11-07T09:46:11.8445718Z   overwrite: false
2026-11-07T09:46:11.8446244Z   include-hidden-files: false
2026-11-07T09:46:11.8446443Z env:
2026-11-07T09:46:11.8446597Z   CC: clang
2026-11-07T09:46:11.8446764Z   CFLAGS: -O2
2026-11-07T09:46:11.8446982Z   pythonLocation: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T09:46:11.8447338Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib/pkgconfig
2026-11-07T09:46:11.8447672Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T09:46:11.8447981Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T09:46:11.8448319Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T09:46:11.8448621Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib
2026-11-07T09:46:11.8448885Z ##[endgroup]
2026-11-07T09:46:11.9751152Z With the provided path, there will be 1 file uploaded
2026-11-07T09:46:11.9772448Z Artifact name is valid!
2026-11-07T09:46:11.9773850Z Root directory input is valid!
2026-11-07T09:46:12.3280624Z Beginning upload of artifact content to blob storage
2026-11-07T09:46:12.5817133Z Uploaded bytes 376
2026-11-07T09:46:12.6426093Z Finished uploading artifact content to blob storage!
2026-11-07T09:46:12.6426847Z SHA256 digest of uploaded artifact zip is ab336c1665c8e90790d62a2a394fdbf7b382ba20158b0f0bc1ea4067414406f2
2026-11-07T09:46:12.6427533Z Finalizing artifact upload
2026-11-07T09:46:13.1576869Z Artifact u2-file-root-fix-1.zip successfully finalized. Artifact ID 13570180948
2026-11-07T09:46:13.1577794Z Artifact u2-file-root-fix-1 has been successfully uploaded! Final size is 376 bytes. Artifact ID is 13570180948
2026-11-07T09:46:13.1578833Z Artifact download URL: https://github.com/eristavi/eristavi-lang/actions/runs/42360810124/artifacts/13570180948
2026-11-07T09:46:13.1752106Z Post job cleanup.
2026-11-07T09:46:13.2999801Z Post job cleanup.
2026-11-07T09:46:13.3792964Z [command]/usr/bin/git version
2026-11-07T09:46:13.3830216Z git version 2.56.0
2026-11-07T09:46:13.3862997Z Temporarily overriding HOME='/home/runner/work/_temp/af6a7659-5a0b-481a-bafc-252735f3d3d5' before making global git config changes
2026-11-07T09:46:13.3864159Z Adding repository directory to the temporary git global config as a safe directory
2026-11-07T09:46:13.3867899Z [command]/usr/bin/git config --global --add safe.directory /home/runner/work/eristavi-lang/eristavi-lang
2026-11-07T09:46:13.3902714Z Removing SSH command configuration
2026-11-07T09:46:13.3909131Z [command]/usr/bin/git config --local --name-only --get-regexp core\.sshCommand
2026-11-07T09:46:13.3944439Z [command]/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'core\.sshCommand' && git config --local --unset-all 'core.sshCommand' || :"
2026-11-07T09:46:13.4203418Z Removing HTTP extra header
2026-11-07T09:46:13.4210119Z [command]/usr/bin/git config --local --name-only --get-regexp http\.https\:\/\/github\.com\/\.extraheader
2026-11-07T09:46:13.4248749Z [command]/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'http\.https\:\/\/github\.com\/\.extraheader' && git config --local --unset-all 'http.https://github.com/.extraheader' || :"
2026-11-07T09:46:13.4477560Z Removing includeIf entries pointing to credentials config files
2026-11-07T09:46:13.4484493Z [command]/usr/bin/git config --local --name-only --get-regexp ^includeIf\.gitdir:
2026-11-07T09:46:13.4521814Z includeif.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git.path
2026-11-07T09:46:13.4522430Z includeif.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git/worktrees/*.path
2026-11-07T09:46:13.4523023Z includeif.gitdir:/github/workspace/.git.path
2026-11-07T09:46:13.4523370Z includeif.gitdir:/github/workspace/.git/worktrees/*.path
2026-11-07T09:46:13.4532073Z [command]/usr/bin/git config --local --get-all includeif.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git.path
2026-11-07T09:46:13.4561489Z /home/runner/work/_temp/git-credentials-3ddfc5bd-1c83-46db-977c-5d0405790193.config
2026-11-07T09:46:13.4571687Z [command]/usr/bin/git config --local --unset includeif.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git.path /home/runner/work/_temp/git-credentials-3ddfc5bd-1c83-46db-977c-5d0405790193.config
2026-11-07T09:46:13.4614301Z [command]/usr/bin/git config --local --get-all includeif.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git/worktrees/*.path
2026-11-07T09:46:13.4643784Z /home/runner/work/_temp/git-credentials-3ddfc5bd-1c83-46db-977c-5d0405790193.config
2026-11-07T09:46:13.4653018Z [command]/usr/bin/git config --local --unset includeif.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git/worktrees/*.path /home/runner/work/_temp/git-credentials-3ddfc5bd-1c83-46db-977c-5d0405790193.config
2026-11-07T09:46:13.4690478Z [command]/usr/bin/git config --local --get-all includeif.gitdir:/github/workspace/.git.path
2026-11-07T09:46:13.4721587Z /github/runner_temp/git-credentials-3ddfc5bd-1c83-46db-977c-5d0405790193.config
2026-11-07T09:46:13.4730252Z [command]/usr/bin/git config --local --unset includeif.gitdir:/github/workspace/.git.path /github/runner_temp/git-credentials-3ddfc5bd-1c83-46db-977c-5d0405790193.config
2026-11-07T09:46:13.4774806Z [command]/usr/bin/git config --local --get-all includeif.gitdir:/github/workspace/.git/worktrees/*.path
2026-11-07T09:46:13.4806138Z /github/runner_temp/git-credentials-3ddfc5bd-1c83-46db-977c-5d0405790193.config
2026-11-07T09:46:13.4816613Z [command]/usr/bin/git config --local --unset includeif.gitdir:/github/workspace/.git/worktrees/*.path /github/runner_temp/git-credentials-3ddfc5bd-1c83-46db-977c-5d0405790193.config
2026-11-07T09:46:13.4866742Z [command]/usr/bin/git submodule foreach --recursive git config --local --show-origin --name-only --get-regexp remote.origin.url
2026-11-07T09:46:13.5092137Z Removing credentials config '/home/runner/work/_temp/git-credentials-3ddfc5bd-1c83-46db-977c-5d0405790193.config'
2026-11-07T09:46:13.5241594Z Cleaning up orphan processes

````
