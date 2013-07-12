from scrapy.item import Item, Field

class OxygendemoItem(Item):
    type = Field()
    gender = Field()
    designer = Field()
    code = Field()
    name = Field()
    description = Field()
    raw_color = Field()
    image_urls = Field()
    gbp_price = Field()
    sale_discount = Field()
    stock_status = Field()
    source_url = Field()