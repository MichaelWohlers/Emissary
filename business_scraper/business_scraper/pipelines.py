# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

from itemadapter import ItemAdapter
from shared import db
from models import Place, Contact


class BusinessScraperPipeline:
    def process_item(self, item, spider):
        return item
    
class ProhibitedSitesPipeline:
    def __init__(self):
        self.prohibited_place_ids = []

    def process_item(self, item, spider):
        if item.get('prohibited'):
            self.prohibited_place_ids.append(item['place_id'])
        return item

    def close_spider(self, spider):
        with open('prohibited_places.txt', 'w') as file:
            for place_id in self.prohibited_place_ids:
                file.write(f"{place_id}\n")

class YourScrapyPipeline:
    def process_item(self, item, spider):
        # Assuming 'place_id' in item is the ID of the Place in your database
        place = Place.query.get(item['place_id'])
        if place:
            contact = Contact(
                email=item.get('email'),
                phone_number=item.get('phone_number'),
                contact_name=item.get('contact_name'),
                contact_title=item.get('contact_title'),
                place=place
            )
            db.session.add(contact)
            db.session.commit()
        return item