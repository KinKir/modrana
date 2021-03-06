//OptionsMapPage.qml

import QtQuick 2.0
import UC 1.0
import "modrana_components"

BasePage {
    id: mapOptionsPage
    headerText : "Map"
    bottomPadding : 0
    property string mapFolderPath : rWin.dcall("modrana.gui.modrana.paths.getMapFolderPath", [],
    qsTr("path lookup in progress"), function(v){mapFolderPath=v})
    property string freeSpace : rWin.dcall("modrana.gui.modules.mapData.getFreeSpaceString", [],
    qsTr("unknown"), function(v){freeSpace=v})

    content : ContentColumn {
        KeyComboBox {
            width : parent.width
            label : qsTr("Store map tiles in")
            key : "tileStorageType"
            model : ListModel {
                ListElement {
                    text : "files"
                    value : "files"

                }
                ListElement {
                    text : "Sqlite"
                    value : "sqlite"
                }
            }
        }
        KeyComboBox {
            label : qsTr("Map scaling")
            key : "mapScale"
            model : ListModel {
                ListElement {
                    text : "off (1x)"
                    value : 1
                }
                ListElement {
                    text : "2x"
                    value : 2
                }
                ListElement {
                    text : "4x"
                    value : 4
                }
            }
            onItemChanged : {
                rWin.log.info("map scale changed to: " + item.value)
                rWin.mapPage.mapTileScale = item.value
            }
        }
        Label {
            text : qsTr("Map folder path:") + newline + mapOptionsPage.mapFolderPath
            property string newline : rWin.inPortrait ? "<br>" : " "
            wrapMode : Text.WrapAnywhere
            width : parent.width
        }
        Label {
            text : qsTr("Free space available: <b>" + mapOptionsPage.freeSpace + "</b>")
            wrapMode : Text.Wrap
            width : parent.width
        }
    }
}
