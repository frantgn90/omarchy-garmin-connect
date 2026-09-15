import QtQuick
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Ui

BarWidget {
  id: root
  moduleName: "garmin.connect"

  readonly property string pluginDir: Quickshell.env("HOME") + "/.config/omarchy/plugins/garmin.connect"
  readonly property string scriptPath: pluginDir + "/garmin-status"
  readonly property string loginScriptPath: pluginDir + "/garmin-login"

  // Last known-good values. Kept as-is across transient errors so the widget
  // never blanks out just because one poll failed (flaky wifi, Garmin's own
  // rate limiting, etc.) -- only a real login problem changes what's shown.
  property int steps: 0
  property int goal: 0
  property int calories: 0
  property var restingHr: null
  property real floors: 0
  property real floorsGoal: 0
  property var bodyBattery: null
  property int intensityMinutes: 0
  property int intensityGoal: 0
  property var stressLevel: null
  property string stressQualifier: ""
  property bool hasData: false
  property bool needsLogin: false

  property bool panelOpen: false
  readonly property real stepsProgress: goal > 0 ? Math.max(0, Math.min(1, steps / goal)) : 0
  readonly property real floorsProgress: floorsGoal > 0 ? Math.max(0, Math.min(1, floors / floorsGoal)) : 0
  readonly property real bodyBatteryProgress: bodyBattery !== null ? Math.max(0, Math.min(1, bodyBattery / 100)) : 0
  readonly property real intensityProgress: intensityGoal > 0 ? Math.max(0, Math.min(1, intensityMinutes / intensityGoal)) : 0

  function refresh() {
    if (!statusProc.running) statusProc.running = true
  }

  function openGarmin() {
    if (root.bar) root.bar.run("xdg-open https://connect.garmin.com/modern")
  }

  function reLogin() {
    if (root.bar) root.bar.run("omarchy-launch-floating-terminal-with-presentation " + Util.shellQuote(root.loginScriptPath))
  }

  // Contract PopupCard's outside-click dismissal relies on (`owner.close()`).
  function close() { panelOpen = false }

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
        root.floors = data.floors || 0
        root.floorsGoal = data.floorsGoal || 0
        root.bodyBattery = data.bodyBattery !== undefined ? data.bodyBattery : null
        root.intensityMinutes = data.intensityMinutes || 0
        root.intensityGoal = data.intensityGoal || 0
        root.stressLevel = data.stressLevel !== undefined ? data.stressLevel : null
        root.stressQualifier = data.stressQualifier || ""
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
      ? "Garmin session expired. Click to re-authenticate (a terminal will open)."
      : "Left click: details · Right click: open Garmin Connect"
    onPressed: function(b) {
      if (root.needsLogin) { root.reLogin(); return }
      if (b === Qt.MiddleButton) root.refresh()
      else if (b === Qt.RightButton) root.openGarmin()
      else root.panelOpen = !root.panelOpen
    }
  }

  // A labeled row plus a horizontal fill bar, for any metric expressed as a
  // fraction of a goal (steps, floors, body battery, intensity minutes).
  component MetricBar: Column {
    id: metricBar
    property string label: ""
    property real progress: 0
    width: parent ? parent.width : 0
    spacing: Style.space(4)

    Text {
      text: metricBar.label
      color: Color.popups.text
      font.family: root.bar ? root.bar.fontFamily : Style.font.family
      font.pixelSize: Style.font.caption
    }

    Rectangle {
      width: parent.width
      height: Style.space(8)
      radius: height / 2
      color: Util.alpha(Color.popups.text, 0.15)

      Rectangle {
        width: parent.width * metricBar.progress
        height: parent.height
        radius: parent.radius
        color: Color.accent

        Behavior on width {
          NumberAnimation { duration: 160; easing.type: Easing.OutCubic }
        }
      }
    }
  }

  PopupCard {
    id: detailsPopup
    anchorItem: button
    owner: root
    bar: root.bar
    open: root.panelOpen
    contentWidth: detailsPopup.fittedContentWidth(Style.space(230))
    contentHeight: detailsPopup.fittedContentHeight(detailsColumn.implicitHeight)

    Column {
      id: detailsColumn
      anchors.fill: parent
      spacing: Style.space(10)

      Text {
        text: "Garmin"
        color: Color.popups.text
        font.family: root.bar ? root.bar.fontFamily : Style.font.family
        font.pixelSize: Style.font.body
        font.bold: true
      }

      MetricBar {
        label: "👣 Steps: " + root.steps + " / " + root.goal
        progress: root.stepsProgress
      }

      MetricBar {
        visible: root.floorsGoal > 0
        label: "🪜 Floors: " + root.floors.toFixed(1) + " / " + root.floorsGoal
        progress: root.floorsProgress
      }

      MetricBar {
        visible: root.bodyBattery !== null
        label: "🔋 Body Battery: " + root.bodyBattery + " / 100"
        progress: root.bodyBatteryProgress
      }

      MetricBar {
        visible: root.intensityGoal > 0
        label: "⏱ Intensity (week): " + root.intensityMinutes + " / " + root.intensityGoal + " min"
        progress: root.intensityProgress
      }

      Text {
        text: "🔥 Calories: " + root.calories + " kcal"
        color: Color.popups.text
        font.family: root.bar ? root.bar.fontFamily : Style.font.family
        font.pixelSize: Style.font.caption
      }

      Text {
        visible: root.restingHr !== null
        text: "❤ Resting HR: " + root.restingHr + " bpm"
        color: Color.popups.text
        font.family: root.bar ? root.bar.fontFamily : Style.font.family
        font.pixelSize: Style.font.caption
      }

      Text {
        visible: root.stressLevel !== null
        text: "😣 Stress: " + root.stressLevel + (root.stressQualifier ? " (" + root.stressQualifier + ")" : "")
        color: Color.popups.text
        font.family: root.bar ? root.bar.fontFamily : Style.font.family
        font.pixelSize: Style.font.caption
      }
    }
  }
}
