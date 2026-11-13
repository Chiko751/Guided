# Changelog

## 1.3.17
**Your Steam profile in the Guide** (*Appearance › Text & icons › Profile*, switch "Steam profile effects", on by default)
- The **avatar frame** you equipped in the Steam Points Shop sits around the profile picture – animated, like in Steam.
- **Frame thickness** (100–300 %): the ring grows outwards, its inner edge stays at the picture.
- **Frame colour**: original, like the banner animation, the running game's colour (as in the Dynamic preset), the accent or a fixed colour – the frame keeps its animation and shading.
- **Round profile pictures** get a round glowing ring in the frame's colour (Steam frames are square artwork).
- **Animated avatars** replace the still picture.
- The (animated) **mini profile background** plays in the name banner behind your name (Modern, Classic and Metro layouts); a still picture with animations off.
- **Player ring in the banner**: glow colour (same choices) and how many quarters are lit (1–4).

**Classic NXE follows your colours**
- The selection bar, window and blades now use the accent, window and tab colour – the glossy two-tone bar, the window shading and the curved blades stay.

**Fixes**
- "Round" profile pictures had no effect in the Classic layout.
- Friends window: the tab row was squeezed to a few pixels on the Discord tabs.
- Metro: switched-on toggles were grey, the active Friends / Controller tab had dark text on the accent.
- Untranslated texts: "No layout" / "Loading…" in the Controller window, "Update Guided" in German.
- Smoother checks: the Windows overlay watcher no longer runs on Linux.

## 1.3.5
- **Steam Input per game** in the Controller window (a game's controller page): a switch "Steam Input for this game" that sets the same option as Steam's game properties, with the note whether it follows Steam's default or is set for this game, and "Reset to Steam default". Like in Steam, with Steam Input off the layouts and button bindings are greyed out and the cursor skips them. Takes effect after the game restarts.
- The update check only offers releases that contain this build's ZIP – the new Windows build (**Guided Windows**, separate pre-releases tagged `windows-v…`) never reaches Linux installs, and vice versa.
- The backend also loads where Unix-only modules are missing (preparation for Windows; nothing changes on Linux).

## 1.3.0
**Discord via Steamcord** (beta feature) – only when the Decky plugin "Steamcord" is installed
- New switch *Settings › Guided › Adapt Steamcord*. It only appears with Steamcord installed; Guided calls Steamcord's own backend for everything and bundles nothing of it.
- Friends window tabs with the switch on: **Favorites | Discord friends | Friends | Servers** (LB / RB).
- **Discord friends**: your Discord direct messages and group chats in Steamcord's order, with status. Open a chat on the right (read and write, B closes it), call, or join a call that is already running.
- **Servers**: your servers with voice channels; pick a channel and press again to join.
- **Party** for Discord: while you are in a Discord voice chat, the main menu shows "Party" with a Discord tag. The Party window shows the members, who is speaking and who is muted, who is still being called, plus mic, sound (deafen), invite (sends the voice channel link to a friend), chat (direct calls) and hang up.
- **Incoming calls** (Steam and Discord): a "<name> is calling" row in the main menu; the Party window says where the call comes from and lets you accept or decline.

**Smoother windows**
- Windows that grow or shrink (Friends, My games, Settings, achievements, plugins) now animate on the GPU: frame, tabs, header and legend move together and the content fades in at the end. Before, every frame re-laid out the whole menu and the width jumped.
- When a big window would reach past the screen edge (e.g. Friends with a large Guide size), the whole Guide shrinks just enough to fit – the header is no longer cut off.

**Fixes**
- The Party buttons had no focus highlight (only "Hang up" stood out) – for Steam and Discord calls.
- Steamcord and other embedded plugins scroll properly inside the Guide.
- Friends tabs no longer wrap or overflow in narrow windows.

**Updates**
- Pre-releases sort below their release, and the update check only offers pre-releases to someone already on a pre-release.

## 1.2.0
**Party – voice chat in the Guide**
- "Voice chat" in the friends list now calls right away – Steam's quick access menu no longer pops up.
- While a call runs (or a friend calls), a **Party** row appears in the main menu under Friends. It opens the Party window: you and your friend with avatars, who is speaking, the call state (ringing, connecting, connected with duration) and buttons for mic, sound, chat and hang up. Incoming calls can be accepted or declined there.
- Back from the Party window leads to the friends list again; the window closes by itself when the call ends.

**Buttons**
- Start, Select, X, Y and "Steam + A" share one list (*Controller & Keyboard › Buttons*): **Steam menu (left)** – Steam's own menu that sits on the Steam button without Guided –, **Steam quick access (QAM, right)**, Steam quick access on its Decky tab (the old "open Steam menu"), every Guided tab and view ("Guided Downloads", "Guided Media Player", pinned plugin tabs, users, notifications, settings), pin plugin and nothing.

**More**
- New switch under *Guided*: with **"My games" off** the main menu goes straight to Steam's library.
- Text input always uses Steam's on-screen keyboard; the built-in keyboard is paused until it is more polished.
- In the friends list and in "My games" up/down keep the column (e.g. stay on the three dots); from a full-width row in Quick settings the cursor lands on the left.
- Settings are loaded right when the plugin starts: "Steam + A" uses your choice even before the Guide was opened, and a change right after start can no longer overwrite your settings with the defaults.

**What's new?** shows these changes once in the main menu after the update.

## 1.1.0
**Fixes**
- **Controller in the game:** closing the Guide with B on a pinned plugin tab left Steam's side menu open (invisibly), so the game got no controller input until the Guide was opened and closed again (reported in Guided360 issue #1). B now closes the same clean way on every tab.
- **NXE banner:** since 1.0 the active blade (name and player ring) sat behind the window or too far left in Modern NXE, Classic NXE, Metro, Modern NXE Dark and Dynamic. The gap and tab-size sliders no longer override the blades' own sizes or move them onto their own layer.
- **Liquid Glass:** the two blades next to the window close up flush (no gap to look through), their names are no longer cut off (e.g. the game and Quick Resume blades), all other blades stay where they are without glass; Metro gets light glass with dark text and a light banner.
- Coming from Guided360: after removing Guided360, Guided reloads itself so the Guide opens right away.

**Faster**
- Settings: the fixed part of the Guide's CSS (fonts included, ~550 KB) is no longer re-read on every change – dragging a slider costs about 60 % less.
- Media Player: the Spotify status is read in one call and the Flatpak check is cached – about 88 % less work per second while the tab is open.
- The "more below" arrow no longer scans the whole window every 300 ms; the active-tab position is set directly instead of through 24 CSS `:has()` rules.

**What's new?** shows these changes once in the main menu after the update.

## 1.0.0 – Guided360 is now Guided
- **New name:** Guided360 is now **Guided** (new repository). The last Guided360 release (1.37.2) updates to Guided; Guided takes over your settings, custom themes and tab order from Guided360 and then removes Guided360. Its settings folder stays as a backup.
- **Steam Deck** is the default preset for new installs.
- **UI sounds** are off by default and are now a choice (*Appearance › Effects & sound › Sounds*: Off / Xbox 360 – more sets to come).
- **Tab position for every layout:** the bar layouts (pills, dock, sidebar list, rail) put their tabs on any side – top, bottom, left or right (*Appearance › Shapes › Tab position*); stacked cards left or right. With gap 0 pills, list and rail sit inside the window like before, with a gap they float next to it. Vertical tab lists are reached with left/right as before.
- **Gap to the window** and **tab size** sliders for every layout, NXE blades included.
- **Liquid Glass is a switch, not a preset:** *Appearance › Colours › Liquid Glass* turns any preset and layout into tinted glass (window, blades, pills, dock, cards), with glass blur and glass opacity. If you used the Liquid Glass preset, you get Modern NXE with the switch on.
- **What's new?**: after an update to a new major or minor version (1.0 → 1.1, not 1.0.1) a row under *Decky* in the main menu opens a window with the most important changes. It disappears once opened, or with *Dismiss*. New installs don't show it.
- Everything from Guided360 1.37.1 (Media Player with track lists, 14 presets, 8 layouts …), see below.

---

# Guided360 (until 1.37)

## 1.37.0
**Media Player, rebuilt after the Xbox 360 media blade**
- Top: *Spotify library* and *YouTube Music library*, each on its own page. Playlists and albums open their **track list** – start a single track (it plays inside its playlist) or "Play all".
- Bottom: **one player** for whatever is playing – cover with a small source badge (Spotify green / YouTube Music red), play/pause, previous, **stop**, next, **shuffle** (handed to the running player) and a floating **volume** scale (up/down, A or B closes); title, time and a progress line underneath, a little equaliser while music plays.
- Only one source plays at a time: starting one pauses the other; if both run (e.g. Spotify started from the phone), the one started last wins.
- Spotify: the whole library (playlists, albums, artists, podcasts, Liked Songs), read from the app itself – no longer only what its sidebar showed. Covers for mixed playlists fixed.
- YouTube Music: Guided always controls its own invisible player, never a YouTube Music tab you opened in Steam's browser; it picks up a sign-in made there automatically, keeps your volume when you switch playlists and replaces its player by itself if it ever stops responding.
- Help: the Tabs page lists the Media Player; the Media Player help describes the new layout.

## 1.36.0
**Media Player**
- New **Media Player** tab (can be hidden under Guided › Tab settings), like the media player in the Xbox 360 guide: **Spotify** or **YouTube Music**, with now playing (cover, title, artist, progress), previous / play-pause / next and your own library.
- Spotify uses the installed Spotify app (Flatpak `com.spotify.Client`, signed in once); Guided starts it invisibly in the background and lists your playlists, albums and Liked Songs.
- YouTube Music runs in an invisible Steam browser; "Sign in to YouTube Music" opens the sign-in in Steam's browser (shared cookies). Without sign-in you get recommendations.
- Music keeps playing while the Guide is closed and while you play; starting one source pauses the other.

**Presets and layouts**
- 14 presets: Xbox (Modern NXE, Classic NXE, Modern NXE Dark, Liquid Glass, Dynamic, Metro), PlayStation (PS5, PS3), Nintendo (Switch light / dark), Steam (Big Picture, 2004), Steam Deck (Deck, OLED). A preset now sets the whole look – colours, shapes, sizes, font and button symbols.
- 8 layouts: Modern, Classic, Metro blades, tabs on top, dock at the bottom, sidebar left, rail right and **stacked cards**. Vertical layouts get a tab list you reach with left (right for the rail), up/down switches tabs; LB/RB work everywhere.
- Window position horizontal and vertical (centre / left / right, top / bottom), with equal margins.
- **One build only:** the former "Clean" build is now the setting *Appearance › Shapes › Banner* (on every page / main page only). If you used Guided360 Clean, install Guided360 and remove the Clean plugin.

**Appearance**
- Profile picture ring on/off, colours and rainbow; more accent, window, tab and text colours.
- "Reset appearance" resets only the look; "Reset all" keeps your custom themes. Custom themes can be renamed (✎).
- PlayStation button symbols centred, glow colours per symbol (✕ blue, ○ red, □ pink, △ green).
- Light windows (e.g. Switch) keep icons, switches, friends and library readable.

**Settings, navigation, plugins**
- Settings restructured: Appearance (Shapes, Colours, Text & symbols, Effects & sound), Guided (page and tab settings), Controller & Keyboard, System & updates, Help. The settings window grows while open; tabs stay visible but locked.
- Back (B) returns to the row that opened a page. Long pages scroll fully to the top/bottom.
- Dropdowns of embedded Decky plugins open in the Guide's own dropdown; after a Steam dialog the Guide returns to the plugin. Plugins can request a wider window (`data-gx-panel-width`).
- "+" install shows a progress bar and a notification when Decky has loaded the plugin.
- Quick settings without gaps when elements are hidden.
- Help rewritten for the current menus and layouts; missing translations added; words no longer break mid-word in narrow windows.
- Fix: no more "missing localization token" errors logged by Steam.

## 1.33.0
- Settings reorganised: Language, Appearance, Elements, Tabs & menu, Quick settings, Performance, Buttons, Keyboard, System & updates, Help. Glow moved to "Effects & sound", monochrome icons to "Buttons", auto-update and reset to "System & updates"; section headings on Elements, Tabs and Buttons.
- Every choice (language, style, shape, font, colours, tab colour, button mapping, Steam + A tab, glyphs …) opens a dropdown instead of cycling through the values.
- Help texts updated. Code clean-up (removed legacy glass tint, old app-switcher row and unused rules).

## 1.32.0 – 1.32.1
- Quick settings in a fixed two-column layout: Wi-Fi | Bluetooth, Airplane mode | Bluetooth devices, Do not disturb | Night mode; text size slider (Steam's display scaling).
- Performance tab with every option of Steam's Performance menu (incl. tearing, half-rate shading, scaling mode/filter, sharpness, TDP, GPU clock); scaling names straight from Steam's own localisation.
- Every element of Quick settings and Performance can be hidden in the settings.
- Predictable up/down navigation on both pages (row above/below, nearest column).
- Small bouncing "more below" arrow when a page scrolls (once you reached the end it stays away until the Guide is closed; can be switched off).
- Button symbol size small / medium / large. Metro shape: blades always flush with the window.

## 1.31.0
- Automatic update check (90 s after start, then every 6 h, one small conditional GitHub request) with a Steam notification; press it to update.
- Button symbols: Xbox, Nintendo (A/B and X/Y swapped) or PlayStation (✕ ○ □ △).

## 1.30.0
- Friends: sorted by latest chat; the chat opens to the right only when you start it (list becomes compact); per-friend buttons for message, voice chat, join game, invite, and a "More" menu (profile, nickname, Remote Play Together, favourites, trade, inventory, remove, block).
- With Steam's own keyboard open the Guide moves right above it and grows.

## 1.29.0 – 1.29.2
- Fix: the in-game blur slider had no effect on HDR displays.
- Shape setting independent of the style; save the current look as a custom theme (also "save game colours" on the Dynamic hero); style picker with delete.
- Keyboard settings: built-in keyboard on/off, size, tools in the keyboard strip; Steam keyboard detection.
- "360 Slate" renamed to "Modern NXE Dark"; tab colour "Like preset".

## 1.28.1
- Fix: quitting a game from the Guide while another game keeps running no longer leaves Steam's own side menu open.

## 1.28.0
- "+" in the Plugins tab opens a ZIP file browser inside the Guide; Decky installs in the background.
- Window colour option "Dynamic" (from the running game's hero); the Dynamic preset uses it by default.
- Window opacity and in-game blur for every preset (Appearance → Colours); the separate Glass page is gone.

## 1.27.1
- "Power" is now called "System & Power" (DE: "System & Energie").

## 1.16 – 1.27.0
- New styles Classic NXE and Metro; all presets on the Xbox 360 layout; Liquid Glass (tint/opacity/blur) and Dynamic (hero colours) reworked; default renamed to Modern-NXE.
- My games, Achievements, Friends tabs, Controller window with binding editor, Quick Resume, power menu with update from GitHub.
- Plugins tab: Decky settings/store/"install from ZIP" buttons, plugin windows grow with their content.
- Settings reorganised; Steam + A tab choice; slider edit mode; header navigation; player ring; glow effect; mono icons; Nunito font.
- Sharper rendering on all resolutions; Xbox 360 open/close animations.

## 1.15.2
- Beta release.

## 1.10 – 1.15
- Running-app switcher at the bottom of the main menu and window list on the in-game tab (experimental).
- Fixes around switching from the Guide to Steam pages, plugin list layout, power view.

## 1.9
- Power view inside the Guide, Slate restyled like the original NXE tabs, smaller tab icons, shorter titles.

## 1.5 – 1.8
- Language selector (English, Deutsch, Español, Français, Português).
- Styles reduced to Xbox 360 (default), 360 Slate, Liquid Glass, Dynamic and Console.
- Dynamic style: colours follow the artwork of the current game.

## Earlier
- Forked from Game Glance by Michael Palma; everything except the menu was removed and the menu re-skinned.
