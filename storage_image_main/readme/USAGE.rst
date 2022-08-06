* Override your model like:

.. code-block:: python

    class ProductProduct(models.Model):

        _name = "product.product"
        _inherit = ["product.product", "storage.main.image.mixin"]
        _field_image_ids = "variant_image_ids"


        # If you want to return the main image not from the first recordset
        # one ordered by sequence, override this method:
        def _filter_main_image_id(self):
            # return <recordset>
