import QtQuick
QtObject {
    property string path: ""
    property bool watchChanges: false
    signal fileChanged()
    signal loaded()
    signal loadFailed(int error)
    function text() { return "" }
    function reload() {}
}
