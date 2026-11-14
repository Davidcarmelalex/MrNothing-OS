# Inherit Google's caiman hardware configuration; do not clone board/AVB policy.
# The release baseline and all proprietary inputs still require ROM-001 review.
ifneq ($(TARGET_BUILD_VARIANT),userdebug)
$(error MrNothing ROM-002 supports engineering userdebug builds only)
endif

$(call inherit-product, device/google/caimito/aosp_caiman.mk)

PRODUCT_NAME := mrnothing_caiman
PRODUCT_DEVICE := caiman
PRODUCT_BRAND := MrNothing
PRODUCT_MODEL := MrNothing OS on Pixel 9 Pro
PRODUCT_MANUFACTURER := Google

PRODUCT_SOONG_NAMESPACES += device/mrnothing/caiman
PRODUCT_PACKAGES += MrNothingLauncher

# Keep the upstream launcher/Quickstep and setup flow as recovery paths.
# No permission grants, default-role overrides, sepolicy or boot-chain changes.
