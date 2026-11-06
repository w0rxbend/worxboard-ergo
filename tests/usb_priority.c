/* SPDX-License-Identifier: GPL-3.0-or-later */
#include <assert.h>
#include "usb_priority.h"
int main(void) {
    assert(ergo_usb_choose(0,-1)==-1);
    assert(ergo_usb_choose(1,-1)==0);
    assert(ergo_usb_choose(2,-1)==1);
    assert(ergo_usb_choose(4,-1)==2);
    assert(ergo_usb_choose(7,-1)==1);
    assert(ergo_usb_choose(7,0)==0);
    assert(ergo_usb_choose(7,2)==2);
    assert(ergo_usb_choose(6,0)==1);
    for (unsigned present=0; present<8; present++) {
        for (int current=-1; current<3; current++) {
            int selected=ergo_usb_choose(present,current);
            assert((selected<0)==(present==0));
            if (selected>=0) { assert(present & (1u<<selected)); }
            if (current>=0 && (present & (1u<<current))) { assert(selected==current); }
        }
    }
}
