from Products.Five import BrowserView


class SlideshowView(BrowserView):
    def get_slides():
        return []

    def get_image(slide):
        pass

    def slide_type(slide):
        pass

    def get_id():
        pass
        # get the id entered in Slideshow schema for custom styling
