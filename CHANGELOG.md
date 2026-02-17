# Changelog

## [1.2.0](https://github.com/legendik/ha-jablotron-volta/compare/jablotron-volta-v1.1.6...jablotron-volta-v1.2.0) (2026-02-17)


### Features

* add professional dashboard with 7 tabs ([c749c93](https://github.com/legendik/ha-jablotron-volta/commit/c749c93a2168d695531ec58ad9c6ce57b1eeb17c))


### Bug Fixes

* add device prefix for all entities ([ccf1352](https://github.com/legendik/ha-jablotron-volta/commit/ccf1352d10b544cc6310d0e364b568e8076cd4df))

## [1.1.6](https://github.com/legendik/ha-jablotron-volta/compare/jablotron-volta-v1.1.5...jablotron-volta-v1.1.6) (2026-02-17)


### Bug Fixes

* use signed conversion for outdoor temperatures ([42f1294](https://github.com/legendik/ha-jablotron-volta/commit/42f12946e7fb17373cce666b7040c92c7af7a31f))

## [1.1.5](https://github.com/legendik/ha-jablotron-volta/compare/jablotron-volta-v1.1.4...jablotron-volta-v1.1.5) (2026-02-17)


### Bug Fixes

* split register reads to avoid non-existent addresses ([69c3eaa](https://github.com/legendik/ha-jablotron-volta/commit/69c3eaa63b04006893c82a4fa147f442aca06654))

## [1.1.4](https://github.com/legendik/ha-jablotron-volta/compare/jablotron-volta-v1.1.3...jablotron-volta-v1.1.4) (2026-02-17)


### Bug Fixes

* authenticate immediately after connection instead of before each read ([101ded3](https://github.com/legendik/ha-jablotron-volta/commit/101ded31bb685c5505f19d1a1672c8cbfebd3145))

## [1.1.3](https://github.com/legendik/ha-jablotron-volta/compare/jablotron-volta-v1.1.2...jablotron-volta-v1.1.3) (2026-02-17)


### Bug Fixes

* authenticate once at start of read_all_data for holding registers ([dc56ad5](https://github.com/legendik/ha-jablotron-volta/commit/dc56ad52b19edc4b37ec010da348ae283b1d0167))


### Miscellaneous

* use releas_please_token ([367c618](https://github.com/legendik/ha-jablotron-volta/commit/367c618627e98be39a0491a36c7f30cebaa876bf))

## [1.1.2](https://github.com/legendik/ha-jablotron-volta/compare/jablotron-volta-v1.1.1...jablotron-volta-v1.1.2) (2026-02-17)


### Bug Fixes

* login before reading holding registers ([c9c4a6d](https://github.com/legendik/ha-jablotron-volta/commit/c9c4a6df469460cd4a564afb00c095022db92c5a))

## [1.1.1](https://github.com/legendik/ha-jablotron-volta/compare/jablotron-volta-v1.1.0...jablotron-volta-v1.1.1) (2026-02-17)


### Bug Fixes

* calls to writing register must be authenticated first ([2e73ec5](https://github.com/legendik/ha-jablotron-volta/commit/2e73ec59dbbae739109c3e5f6008555250cf27f6))

## [1.1.0](https://github.com/legendik/ha-jablotron-volta/compare/jablotron-volta-v1.0.0...jablotron-volta-v1.1.0) (2026-02-17)


### Features

* arguments update ([5b6b673](https://github.com/legendik/ha-jablotron-volta/commit/5b6b67389a5b50e4cba7531cc2296bc32069a524))
* better debug messages ([1203de1](https://github.com/legendik/ha-jablotron-volta/commit/1203de1a89abc47331eb97726e4f0c2d73096185))
* init ([#1](https://github.com/legendik/ha-jablotron-volta/issues/1)) ([eed0464](https://github.com/legendik/ha-jablotron-volta/commit/eed04644d04505dfe98229446f58863a9897e1ba))
* init hacs ([2b290fb](https://github.com/legendik/ha-jablotron-volta/commit/2b290fb18ca442667c77d0c8b28035739100430e))
* update pymodbus ([7b624c1](https://github.com/legendik/ha-jablotron-volta/commit/7b624c1e87c38ac2a7225d3695df61b5509c6ba2))


### Bug Fixes

* add explicit GITHUB_TOKEN to release-please action ([dff3186](https://github.com/legendik/ha-jablotron-volta/commit/dff318678e8a1134a95c8d50611796e025711f6c))
* do not use exact version of pymodbus ([ff22373](https://github.com/legendik/ha-jablotron-volta/commit/ff223738c5214d80255d203553ed0048f10e9b2a))
* modbus address updates ([e6f16a4](https://github.com/legendik/ha-jablotron-volta/commit/e6f16a46704d4bda41f5f45a2660042aaef25f27))
* remove invalid keys from hacs.json ([f252e19](https://github.com/legendik/ha-jablotron-volta/commit/f252e19383be3db5dae9ad91c274e5b915954b22))
* slave -&gt; unit ([9878a90](https://github.com/legendik/ha-jablotron-volta/commit/9878a90057933dde1f284c87053a265478b78c1d))
* temperatures - int vs uint ([f4958b4](https://github.com/legendik/ha-jablotron-volta/commit/f4958b49bd1102d5bf9c651e02718d232fc921e4))


### Miscellaneous

* add requirements for dev ([41ba79b](https://github.com/legendik/ha-jablotron-volta/commit/41ba79b543169384e953ba14df052d97b3ab6046))
* add validate action and release please ([fbf6fcd](https://github.com/legendik/ha-jablotron-volta/commit/fbf6fcdcecc882897972a521d3b2c8d222ad592e))
* update hacs file ([16ea58b](https://github.com/legendik/ha-jablotron-volta/commit/16ea58bc584b63b75a03107e5490a1847d5bcf54))
