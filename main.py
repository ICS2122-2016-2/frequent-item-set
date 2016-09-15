import os
import json

__author__ = "rpalmaotero"


N_POSITIONS = 12750
N_FREQ_ITEMS_SET = 60
MAX_FREQ_ITEMS_SET_LENGTH = N_POSITIONS // N_FREQ_ITEMS_SET
DB_PATH = os.path.join(os.path.dirname(__file__), "./cleaned_db.dat")
OUTPUT_FILENAME = "families.json"


class FrequentItemsSets:
    def __init__(self):
        self.affinities = {}
        self.families = {}

        self.get_products()
        self.get_top_products()
        self.assign_products_to_families()
        self.output_families()

    def get_products(self):
        with open(DB_PATH) as db_file:
            for receipt_line in db_file:
                skus = set(map(int, receipt_line.strip().split(" ")))
                for sku in skus:
                    if sku in self.affinities:
                        self.update_affinities_record(sku, skus - set([sku]))
                    else:
                        self.create_affinities_record(sku, skus - set([sku]))

    def update_affinities_record(self, sku, other_skus):
        self.affinities[sku]["n_times"] += 1
        for other_sku in other_skus:
            if other_sku in self.affinities[sku]["affinities"]:
                self.affinities[sku]["affinities"][other_sku] += 1
            else:
                self.affinities[sku]["affinities"][other_sku] = 1

    def create_affinities_record(self, sku, other_skus):
        self.affinities[sku] = {"n_times": 0, "affinities": {}}
        self.update_affinities_record(sku, other_skus)

    def get_top_products(self):
        top_products = list(map(
            lambda product: product[0],
            sorted(
                map(
                    lambda affinity: (affinity[0], affinity[1]["n_times"]),
                    self.affinities.items()
                ),
                key=lambda record: record[1],
                reverse=True
            )[:N_FREQ_ITEMS_SET]
        ))

        for top_product in top_products:
            self.families[top_product] = []
            del self.affinities[top_product]

    #TODO: fijarnos en sku a sku? fijarnos directamente en afinidad de tops?
    def assign_products_to_families(self):
        left_alone = 0
        for sku, record in self.affinities.items():
            top_affinities = sorted(
                filter(
                    lambda item: item[0] in self.families,
                    record["affinities"].items()
                ),
                key=lambda item: item[1],
                reverse=True
            )

            inserted = False
            for top_sku, _ in top_affinities:
                if len(self.families[top_sku]) < MAX_FREQ_ITEMS_SET_LENGTH - 1:
                    self.families[top_sku].append(sku)
                    inserted = True
                    break

            if not inserted:
                left_alone += 1
                print("WARNING: {} left alone...".format(sku))

        print("WARNING: {} SKUs left alone...".format(left_alone))

    def output_families(self):
        families = list(map(
            lambda family: [family[0]] + family[1],
            self.families.items()
        ))
        with open(OUTPUT_FILENAME, "w") as output_file:
            json.dump(families, output_file)


if __name__ == "__main__":
    FrequentItemsSets()
