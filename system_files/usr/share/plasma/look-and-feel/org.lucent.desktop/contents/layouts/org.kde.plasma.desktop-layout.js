// Lucent OS default layout, applied by plasmashell on a user's first login.
// Uses only the stock Plasma 6 desktop scripting API.
//
//  * top bar:   [launcher]  ............................  [tray] [clock]
//  * dock:      floating, centred, sized to its icons; an icons-only task
//               manager that behaves like the Windows taskbar (running
//               windows grouped per app, hover thumbnails, click = minimise
//               or restore).
// There is deliberately no global menu: Flatpak/GTK/Electron apps
// (ONLYOFFICE, GIMP, Firefox...) mostly don't export one, and Windows users
// expect menus inside the window.

var desktopsArray = desktopsForActivity(currentActivity());
for (var i = 0; i < desktopsArray.length; i++) {
    var d = desktopsArray[i];
    d.wallpaperPlugin = "org.kde.image";
    d.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    d.writeConfig("Image", "file:///usr/share/wallpapers/Lucent/");
}

// ---- Top bar ---------------------------------------------------------------
var top = new Panel;
top.location = "top";
top.height = Math.round(gridUnit * 1.6);
top.floating = false;
top.hiding = "none";

var launcher = top.addWidget("org.kde.plasma.kickoff");
launcher.currentConfigGroup = ["General"];
launcher.writeConfig("icon", "lucent-start");
launcher.writeConfig("favoritesPortedToKAstats", true);
launcher.currentConfigGroup = ["Shortcuts"];
launcher.writeConfig("global", "Alt+F1");

top.addWidget("org.kde.plasma.panelspacer");
top.addWidget("org.kde.plasma.systemtray");

var clock = top.addWidget("org.kde.plasma.digitalclock");
clock.currentConfigGroup = ["Appearance"];
clock.writeConfig("showDate", true);
clock.writeConfig("dateDisplayFormat", "BesideTime");

// ---- Dock (taskbar) ----------------------------------------------------------
var dock = new Panel;
dock.location = "bottom";
dock.height = Math.round(gridUnit * 3);
dock.lengthMode = "fit";
dock.alignment = "center";
dock.floating = true;
dock.hiding = "none";

var tasks = dock.addWidget("org.kde.plasma.icontasks");
tasks.currentConfigGroup = ["General"];
tasks.writeConfig("launchers", [
    "applications:org.kde.dolphin.desktop",
    "applications:org.mozilla.firefox.desktop",
    "applications:org.onlyoffice.desktopeditors.desktop",
    "applications:org.kde.okular.desktop",
    "applications:org.kde.discover.desktop",
    "applications:systemsettings.desktop"
]);
tasks.writeConfig("groupingStrategy", 1);          // group windows by app
tasks.writeConfig("groupedTaskVisualization", 1);  // click group = thumbnails
tasks.writeConfig("showToolTips", true);           // hover = live thumbnail
tasks.writeConfig("highlightWindows", true);
tasks.writeConfig("minimizeActiveTaskOnClick", true);
tasks.writeConfig("indicateAudioStreams", true);
