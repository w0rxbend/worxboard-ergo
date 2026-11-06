/* SPDX-License-Identifier: GPL-3.0-or-later */
/* TI TS3USB3031: 00 left, 01 center, 10 right, 11 high impedance.
 * Cold boot priority: center -> left -> right. Retain selection while powered.
 * Each VBUS is sensed before its isolation diode through a 10k/10k divider.
 * Board-level routing and hardware switching behavior are not yet validated.
 */
#include "usb_priority.h"
#include <zephyr/device.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/init.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(ergo_usb, LOG_LEVEL_INF);
static const struct device *const gpio = DEVICE_DT_GET(DT_NODELABEL(gpio0));
static struct k_work_delayable poll;
static int selected = -1;
static const gpio_pin_t sense[] = {23, 24, 25};
static void mux_off(void) {
    gpio_port_set_masked(gpio, BIT(21) | BIT(22), BIT(21) | BIT(22));
}
static void update(struct k_work *work) {
    ARG_UNUSED(work);
    if (selected >= 0 && gpio_pin_get(gpio, sense[selected]) > 0) {
        k_work_reschedule(&poll, K_MSEC(100));
        return;
    }
    mux_off();
    selected = -1;
    k_msleep(25); /* disconnect interval, then debounce VBUS */
    unsigned present = 0;
    for (int i = 0; i < 3; i++) {
        if (gpio_pin_get(gpio, sense[i]) > 0) { present |= BIT(i); }
    }
    selected = ergo_usb_choose(present, -1);
    if (selected >= 0) {
        /* HIZ -> 01/10/00. For 00, intermediate 01 exists briefly on boot;
         * use the RP2040 atomic masked GPIO alias for both select bits. */
        const uint32_t mask = BIT(21) | BIT(22);
        const uint32_t value = ((uint32_t)selected << 21);
        gpio_port_set_masked(gpio, mask, value);
        LOG_INF("USB input %d (0 left, 1 center, 2 right)", selected);
    }
    k_work_reschedule(&poll, K_MSEC(100));
}
static int selector_init(void) {
    if (!device_is_ready(gpio)) { return -ENODEV; }
    int rc = gpio_pin_configure(gpio, 21, GPIO_OUTPUT_HIGH);
    if (rc) { return rc; }
    rc = gpio_pin_configure(gpio, 22, GPIO_OUTPUT_HIGH);
    if (rc) { return rc; }
    for (int i=0; i<3; i++) {
        rc = gpio_pin_configure(gpio, sense[i], GPIO_INPUT);
        if (rc) { return rc; }
    }
    k_work_init_delayable(&poll, update);
    k_work_schedule(&poll, K_MSEC(50));
    return 0;
}
SYS_INIT(selector_init, APPLICATION, 50);
