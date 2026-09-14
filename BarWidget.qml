import QtQuick
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Ui

BarWidget {
  id: root
  moduleName: "jfmarve.garmin"

  readonly property string pluginDir: Quickshell.env("HOME") + "/.config/omarchy/plugins/jfmarve.garmin"
  readonly property string scriptPath: pluginDir + "/garmin-status"
  readonly property string loginScriptPath: pluginDir + "/garmin-login"

  // Last known-good values. Kept as-is across transient errors so the widget
  // never blanks out just because one poll failed (flaky wifi, Garmin's own
  // rate limiting, etc.) -- only a real login problem changes what's shown.
  property int steps: 0
  property int goal: 0
  property int calories: 0
  property var restingHr: null
  property bool hasData: false
  property bool needsLogin: false

  function refresh() {
    if (!statusProc.running) statusProc.running = true
  }

  function openGarmin() {
    if (root.bar) root.bar.run("xdg-open https://connect.garmin.com/modern")
  }

  function reLogin() {
    if (root.bar) root.bar.run("omarchy-launch-floating-terminal-with-presentation " + Util.shellQuote(root.loginScriptPath))
  }

  // Visible once we have real numbers to show, and also while login is
  // needed -- that state is exactly what the user must not miss.
  visible: hasData || needsLogin
  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  Process {
    id: statusProc
    command: [root.scriptPath]
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        var data
        try {
          data = JSON.parse(String(text || "").trim())
        } catch (e) {
          return // garbage/empty output: ignore, keep last known-good state
        }

        if (data.needsLogin) {
          root.needsLogin = true
          return // keep last known-good steps/calories displayed underneath
        }
        if (data.error) return // transient error: leave last-good state alone

        root.steps = data.steps || 0
        root.goal = data.goal || 0
        root.calories = data.calories || 0
        root.restingHr = data.restingHr || null
        root.hasData = true
        root.needsLogin = false
      }
    }
  }

  Timer {
    interval: 900000
    running: true
    repeat: true
    triggeredOnStart: true
    onTriggered: root.refresh()
  }

  WidgetButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: root.needsLogin ? "⚠ Garmin" : ("👣 " + root.steps)
    fontSize: Style.font.caption
    horizontalMargin: 6
    tooltipText: root.needsLogin
      ? "Sesion de Garmin caducada. Clic para reautenticar (se abrira una terminal)."
      : "Pasos: " + root.steps + " / " + root.goal
        + "\nCalorias: " + root.calories + " kcal"
        + (root.restingHr ? ("\nFC reposo: " + root.restingHr + " ppm") : "")
    onPressed: function(b) {
      if (root.needsLogin) { root.reLogin(); return }
      if (b === Qt.MiddleButton) root.refresh()
      else root.openGarmin()
    }
  }
}
