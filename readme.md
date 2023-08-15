[![Pytest](https://github.com/devnicg/playstvrecovery/actions/workflows/python-app.yml/badge.svg?branch=main)](https://github.com/devnicg/playstvrecovery/actions/workflows/python-app.yml)

# Plays.tv Recovery
A simple tool to recover deleted Plays.tv clips. Plays.tv was shut down on December 15, 2019. Approximately 1/10 of the content was saved and archived by the [Plays TV Archive team](https://wiki.archiveteam.org/index.php/Plays.tv). Being made available through the [Wayback Machine](https://archive.org/web/). This simple tool queries the archive for a given username. Given an archive copy is available, it queries for all available videos and attempts to download them in the highest resolution available.


# Installation & Usage
1. Install the package
   ```
   pip install playstvrecovery
   ```
1. Call the package from the shell
   ```
   playstvrec --user=USERNAME --output-path=EXISTING_DIR
   ```
