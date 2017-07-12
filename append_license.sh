#!/bin/bash
# This file is part of skymod.
# 
# skymod is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# skymod is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with skymod.  If not, see <http://www.gnu.org/licenses/>.

fpath="$1"

if ! [ -f "$fpath" ]; then
	echo "Not a file"
	exit 1
fi

LICENSE="LICENSE.header"

license_text=$(cat $LICENSE)
file_text=$(cat $fpath)

if [[ "$file_text" == "$license_text"* ]]; then
	echo "The license is already in place"
	exit 0
fi

echo "$license_text" | cat - "$fpath" > /tmp/out && cat /tmp/out > "$fpath"
