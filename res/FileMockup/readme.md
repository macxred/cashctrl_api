* These files and folders are used to test/implement the mirror functionality
  - Init is the starting point, the files on the CC server must manually setup to this
    state. If there are additional files on the server they will (should be)
    downloaded to the local computer
  - Rev<number> are subsequent states used for testing

* The '0All' folder corresponds to the 'Alle Dateien' Pseudo-Kategorie in the
  Kategorien sidebar. It is treated as the root and won't be synced

* Further notes:
  - as you can see from strings like 'Alle Dateien', there is a language dependency.
    At the moment it has not been researched how this influences the mirroring. In any
    case this is not good (FIXME)
  - in the UI there is a Filter Checkbox where you can enable ***Ohne Dateien in
    Unterkategorien***. Afterwards it feels much more like a real filesystem...

