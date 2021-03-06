#!/usr/bin/env python
# FormatCBFFullPilatus.py
#   Copyright (C) 2017 Diamond Light Source, Richard Gildea
#
#   This code is distributed under the BSD license, a copy of which is
#   included in the root directory of this package.
#
# Pilatus implementation of fullCBF format, for use with Dectris detectors.

from __future__ import absolute_import, division, print_function

from dxtbx.format.FormatCBFFullPilatus import FormatCBFFullPilatus

# import pycbf

# from dxtbx.format.FormatPilatusHelpers import determine_pilatus_mask


class FormatCBFFullPilatusDLS6MSN126(FormatCBFFullPilatus):
    """An image reading class for full CBF format images from Pilatus
    detectors."""

    @staticmethod
    def understand(image_file):
        """Check to see if this looks like an CBF format image, i.e. we can
        make sense of it."""

        # this depends on DIALS for the goniometer shadow model; if missing
        # simply return False

        try:
            from dials.util.masking import GoniometerShadowMaskGenerator  # test import
        except ImportError:
            return False

        header = FormatCBFFullPilatus.get_cbf_header(image_file)

        for record in header.split("\n"):
            if (
                "# Detector" in record
                and "PILATUS" in record
                and "S/N 60-0126" in header
            ):
                return True

        return False

    @staticmethod
    def has_dynamic_shadowing(**kwargs):
        import libtbx

        dynamic_shadowing = kwargs.get("dynamic_shadowing", False)
        if dynamic_shadowing in (libtbx.Auto, "Auto"):
            return True
        return dynamic_shadowing

    def __init__(self, image_file, **kwargs):
        """Initialise the image structure from the given file."""

        import libtbx
        from dxtbx import IncorrectFormatError

        if not self.understand(image_file):
            raise IncorrectFormatError(self, image_file)

        self._dynamic_shadowing = self.has_dynamic_shadowing(**kwargs)
        FormatCBFFullPilatus.__init__(self, image_file, **kwargs)

    def get_mask(self, goniometer=None):
        mask = super(FormatCBFFullPilatusDLS6MSN126, self).get_mask()

        # when device was installed with SmarGon on I03 this was the signature
        # now it lives on i02-1 => detect - at the moment device has single
        # axis in new home
        if len(self.get_goniometer().get_names()) == 3 and self._dynamic_shadowing:
            gonio_masker = self.get_goniometer_shadow_masker(goniometer=goniometer)
            scan = self.get_scan()
            detector = self.get_detector()
            shadow_mask = gonio_masker.get_mask(detector, scan.get_oscillation()[0])
            assert len(mask) == len(shadow_mask)
            for m, sm in zip(mask, shadow_mask):
                if sm is not None:
                    m &= sm
        return mask

    def get_goniometer_shadow_masker(self, goniometer=None):
        if goniometer is None:
            goniometer = self.get_goniometer()

        if not goniometer or not len(self.get_goniometer().get_names()) == 3:
            return None  # No dynamic shadowing available

        if goniometer.get_names()[1] == "GON_CHI":
            # SmarGon
            from dxtbx.format.SmarGonShadowMask import SmarGonShadowMaskGenerator

            return SmarGonShadowMaskGenerator(goniometer)

        else:
            raise RuntimeError(
                "Don't understand this goniometer: %s" % list(goniometer.get_names())
            )


if __name__ == "__main__":

    import sys

    for arg in sys.argv[1:]:
        print(FormatCBFFullPilatus.understand(arg))
