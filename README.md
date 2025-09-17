Open Source replacement for MainUI on Miyoo and Trim Devices
and potentially others in the future

## Features
- Faster frontend launcher written in Python
- Full compatability with stock Miyoo apps/emulators
- Full compatability with stock MuOS apps/emulators
- Improved themeing support (Can use all Miyoo/OnionOS themes. Daijisho themes can be used with minor modifications)


Still a WIP but works on the Miyoo Flip and partial compatibility on the TrimUI Brick

| Device | Added | Status |
| -- | -- | -- |
| Miyoo Flip | 865f7a3 | Supported |
| RG34XXSP (MuOS Goose)* | c12f38b | Supported |
| RG28XX (MuOS Goose)* | c12f38b | Supported |
| RG34XX (MuOS Goose)* | c12f38b | In Progress |
| RGXX Others (MuOS Goose)* | c12f38b | Untested |
| TrimUI Brick | 865f7a3 | Supported |

* NOTE: There is a PR up to allow launching to an app on startup in MuOS. Hopefully this will be an option soon after the MuOS Canada Goose release. 

In the meantime you can have PyUI apply this patch by going into 

1) Settings -> Extra Settings -> 'Set PyUI as Startup".
2) Rebooting your device
3) Launching PyUI

From now on when you reboot PyUI will be the app launched on startup

## Thanks
- Spruce team w/ special thanks to
   -  Ry - Ryan Sartor 
   -  SundownerSport
   -  Testers from the Spruce Discord and 
      -  Special thanks to KuroZero for their testing and detailed reports
- Shaun Inman - Development on MinUI making it easier to learn how to interact with the hardware
- MuOS - For making running on devices support by MuOS much easier
- Rest of the community that has helped document how these handhelds work

## License

BSD 3-Clause License (Non-Commercial Use with Commercial Use by Permission)

Copyright (c) 2025, Christopher Jacobs
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted **for non-commercial purposes only**, provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions, and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions, and the following disclaimer in the documentation and/or other materials provided with the distribution.

3. Neither the name of Christopher Jacobs nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

4. **Attribution**: When using or distributing the Software (modified or unmodified), you must include the following attribution in a prominent place:
   - The Software's name.
   - The copyright notice: **Copyright (c) 2025 Christopher Jacobs**.
   - A statement that the Software is used under the terms of this license.
   - If the Software is used in a product, application, or publicly visible project, a credit must be included in any user-facing "Credits", "About", or similar section, clearly identifying the Software and the original author.

5. **Commercial Use**: Commercial use of this software is prohibited without explicit, prior written permission from the copyright holder. This includes, but is not limited to:
   - Using the Software or derivative works in products or services for which payment, subscription, or compensation is requested.
   - Offering the Software or services derived from it in exchange for **donations**, **pay-what-you-want models**, or **any other form of voluntary or suggested payment**, if payment is mandatory for access.

6. **Notification Requirement**: Use of this Software under the non-commercial terms, including redistribution or creation of derivative works, requires notification to the original author. This notification must include a brief description of the intended use and a means of contact, and must be sent to:

   - Email: **mainpyui@gmail.com**  
   - Discord: **@chrisbastion**

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
