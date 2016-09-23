import os
import json
import csv
import random

__author__ = "rpalmaotero"


N_POSITIONS = 12750
N_LARGE_ITEMS_SET = 30
N_SMALL_ITEMS_SET = 30
N_ITEMS_SET = N_LARGE_ITEMS_SET + N_SMALL_ITEMS_SET
MAX_LARGE_ITEMS_SET_LENGTH = 225
MAX_SMALL_ITEMS_SET_LENGTH = 200
DB_PATH = os.path.join(os.path.dirname(__file__), "./cleaned_db.dat")
OUTPUT_FILENAME = "families"


class Family(list):
    def __init__(self, max_length):
        super().__init__()

        # privado?
        self.MAX_LENGTH = max_length

    @property
    def full(self):
        return self.MAX_LENGTH - 1 <= len(self)

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
            )[:N_ITEMS_SET]
        ))

        for i, top_product in enumerate(top_products):
            if i >= 30:
                family = Family(MAX_LARGE_ITEMS_SET_LENGTH)
            else:
                family = Family(MAX_SMALL_ITEMS_SET_LENGTH)
            self.families[top_product] = family
            del self.affinities[top_product]

    #TODO: fijarnos en sku a sku? fijarnos directamente en afinidad de tops?
    def assign_products_to_families(self):
        left_alone = []
        for sku, record in self.affinities.items():
            sorted_affinities = sorted(
                record["affinities"].items(),
                key=lambda item: item[1],
                reverse=True
            )
            top_affinities = filter(
                    lambda item: item[0] in self.families,
                    sorted_affinities
            )
            inserted = False
            for top_sku, _ in top_affinities:
                if not self.families[top_sku].full:
                    self.families[top_sku].append(sku)
                    inserted = True
                    break

            if not inserted:
                # Si no entra a ninguna familia...
                # DRY!!!
                other_affinities = filter(
                    lambda item: item[0] not in self.families,
                    sorted_affinities
                )
                for other_sku, _ in other_affinities:
                    for family_sku, family in self.families.items():
                        if other_sku in family and not family.full:
                            family.append(sku)
                            inserted = True
                            break
                    if inserted:
                        break

            if not inserted:
                left_alone.append(sku)
                print("WARNING: {} left alone...".format(sku))
                print(record)
                print("\n", end="")


        print("INFO: {} SKUs left alone...".format(left_alone))

        random.shuffle(left_alone)
        for left_alone_sku in left_alone:
            for _, family in self.families.items():
                if not family.full:
                    family.append(left_alone_sku)
                    break

        print("INFO: So far...")

        for family_sku, family in self.families.items():
            print("INFO: {} family ({} capacity) has {} SKUs...".format(
                family_sku,
                family.MAX_LENGTH,
                len(family) + 1
            ))



    def output_families(self):
        families = list(map(
            lambda family: [family[0]] + family[1],
            sorted(
                self.families.items(),
                key=lambda item: len(item[1])
            )
        ))

        with open("{}.json".format(OUTPUT_FILENAME), "w") as output_file:
            json.dump(families, output_file)

        with open("{}.csv".format(OUTPUT_FILENAME), "w") as output_file:
            writer = csv.writer(output_file)
            writer.writerows(families)


if __name__ == "__main__":
    FrequentItemsSets()
