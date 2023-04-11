# The last version control you will ever need - only for Blender!

No more making copies of your blender project with arbitrary namings, only to forget what is exactly inside them. Checkout features

**INSERT PRESENTATION VIDEO IN FIRESHIP STYLE (BLENDER BACKUP IN 100 SECONDS**

## Features

- Automatically start version control on new projects (toggleable): (insert gif)
- Quickly save a backup after each save with the backup dialog (toggleable): (insert gif)
- Browse through all saved backups of the current project in the Version Control panel: (gif)
- Go back to a savepoint at any time, and continue development without any trouble.
- Want to go back and make serious changes from further saves? Initialize a new timeline, and work from the selected starting point
- Select if previous saves should go along with the new timeline or not
- Easily add, edit, or remove timelines!
- Clear unnecessary saves from the history by removing them\*
  \*This won't delete the backup from disk, see more details [**here**](sasd)
- Check how much storage space your backups are taking with each new save
- Finished project and want to clear out backups? Just head over to preferences and delete version control from the project. Done.
- Want to save versions of texture files along with the project? You got it! check out [**here**](asdasd) how to make it work

## How to use it

Plain and simple. Download the addon and install it like any other. Done!

**Note**: The first time you activate it, it will take some time to load.
**For Windows**: Run Blender as administrator the first time you install Blender Backup in the desired Blender version. ([click here for details](details)).

There's also a known bug if you are running Blender in portable mode (zip). [Click here](Click%20here) to know more about how to get around that.

## How it works

Blender backup uses [Git](https://git-scm.com/about) behind the curtains to keep track of changes and save versions

### Future changes roadmap

- [ ] Automatic incremental version counter with control for major versions (v1.0, v1.1, v1.2... v2.0, v2.1... etc)
- [ ] Search for backups by description or version
- [ ] Action button to undo last save
- [ ] Action button to edit selected save description
- [ ] Editable file/folder(s) pattern that gets versioned along with project (instead of just "/textures" folder)
- [ ] Action button to delete unused backups that got removed but are still in disk (garbage collector)
- [ ] Show size of each backup in the list
- [ ] Cloud services integration
- [ ] Custom Icons
- [ ] Refactor addon for Blender 2.8 - only if desired by community
- [ ] Auto updater - maybe, probably not necessary
