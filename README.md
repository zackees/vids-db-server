# vids_db_server

Server for storing video information.

## Platform Unit Tests

[![Actions Status](https://github.com/zackees/vids-db-server/workflows/MacOS_Tests/badge.svg)](https://github.com/zackees/vids-db-server/actions/workflows/test_macos.yml)
[![Actions Status](https://github.com/zackees/vids-db-server/workflows/Win_Tests/badge.svg)](https://github.com/zackees/vids-db-server/actions/workflows/test_win.yml)
[![Actions Status](https://github.com/zackees/vids-db-server/workflows/Ubuntu_Tests/badge.svg)](https://github.com/zackees/vids-db-server/actions/workflows/test_ubuntu.yml)


# Demo

  * `pip install vids-db-server`
  * `vids_db_server --port 1234`
  * Now open up `http://127.0.0.1:1234` in a browser.

# Demo from github

  * `git clone https://github.com/zackees/vids-db-server`
  * `cd vids_db_server`
  * `pip install -e .`
  * `run_dev.sh` (Browser will open up automatically)

# Docker Production test

  * `git clone https://github.com/zackees/vids-db-server`
  * `cd vids_db_server`
  * `docker-compose up`
  * Now open up `http://127.0.0.1:80/`

# Full Tests + linting

  * `git clone https://github.com/zackees/vids-db-server`
  * `cd vids_db_server`
  * `tox`

