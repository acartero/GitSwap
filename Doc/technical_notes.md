[Home](../readme.md)

Known bugs and missing features
===============================

The following features are not yet present, but should arrive soon:
- Submodules management.
- Slightly less paranoid conflict detection.
- Font size settings.

This tool is a very early proof of concept, and is not yet thoroughly tested: expect slowdowns, crashes and incompatibilities with your environment

List of bugs (will be moved to the bug tracker later): 
- "\ No newline at end of file" may be incorrectly managed in some edge cases.
- This tool may deal incorrectly with Windows and Linux End Of Lines.
- Initial commit's diff is not correctly retrieved.
- Crash on commits adding empty files.

Developer's notes
=================
- This code is neither documented nor "cleaned up".
- Nothing is optimized yet (patches are hand-parsed from git commands, instead of using a dedicated library)
- Used https://www.draw.io/ for the diagram.
