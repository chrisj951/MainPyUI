#!/bin/sh

ENABLED_FILE="/mnt/SDCARD/App/PyUI/enabled"

if [ -e "$ENABLED_FILE" ]; then
    rm -f "$ENABLED_FILE"
    echo "Disabled PyUI (removed $ENABLED_FILE)"
else
    touch "$ENABLED_FILE"
    echo "Enabled PyUI (created $ENABLED_FILE)"

    # Update Themes
    UPDATE_DIR="/mnt/SDCARD/App/PyUI/Themes"
    THEME_DIR="/mnt/SDCARD/Themes/"
    CHECK_FILE="$THEME_DIR/Silky by DiMo/config_750x560.json"

    if [ ! -f "$CHECK_FILE" ]; then
        echo "Config not found, copying update files..."
        cp -r "$UPDATE_DIR" "$THEME_DIR/"
        echo "Update applied."
    else
        echo "Config already exists, nothing to do."
    fi

    # Update runtime.sh
    set -e

    RUNTIME_FILE="/mnt/SDCARD/.tmp_update/runtime.sh"

    if [ ! -f "$RUNTIME_FILE" ]; then
        echo "Error: file not found: $RUNTIME_FILE" >&2
        exit 2
    fi

    # Only proceed if "PyUI" does NOT already occur in the file
    if ! grep -q "PyUI" "$RUNTIME_FILE"; then
        BACKUP="${RUNTIME_FILE}.bak.$(date +%s)"
        cp -p "$RUNTIME_FILE" "$BACKUP"
        echo "Backup created: $BACKUP"

        awk '
        {
            a[++n] = $0
        }
        END {
            i = 1
            while (i <= n) {
                if (i + 3 <= n
                    && a[i]   ~ /PATH=.*miyoodir.*\\$/ 
                    && a[i+1] ~ /LD_LIBRARY_PATH=.*miyoodir\/lib.*\\$/ 
                    && a[i+2] ~ /LD_PRELOAD=.*libpadsp\.so.*\\$/ 
                    && a[i+3] ~ /(^|[[:space:]])\.\/MainUI[[:space:]]*>[[:space:]]*\/dev\/null[[:space:]]*2>&1/ ) {

                    print "    if [ -f /mnt/SDCARD/App/PyUI/enabled ]; then"
                    print "        /mnt/SDCARD/App/PyUI/launch.sh"
                    print "    else"
                    print "        PATH=\"$miyoodir/app:$PATH\" \\"
                    print "        LD_LIBRARY_PATH=\"$miyoodir/lib:/config/lib:/lib\" \\"
                    print "        LD_PRELOAD=\"$miyoodir/lib/libpadsp.so\" \\"
                    print "        ./MainUI > /dev/null 2>&1"
                    print "    fi"
                    i += 4
                } else {
                    print a[i]
                    i++
                }
            }
        }
        ' "$RUNTIME_FILE" > "${RUNTIME_FILE}.new"

        if [ -s "${RUNTIME_FILE}.new" ]; then
            mv "$RUNTIME_FILE.new" "$RUNTIME_FILE"
            echo "Replacement complete in: $RUNTIME_FILE"
        else
            rm -f "$RUNTIME_FILE.new"
            echo "No changes made (no matching block found)."
        fi
    else
        echo "Skipping: File already contains PyUI, no changes made."
    fi

    exit 0

fi

