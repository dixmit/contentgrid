In order to create an integration between contentgrid and Odoo we must follow this
steps:

1. Access in Developer Mode your Odoo instance
2. Access the menu _Settings / Technical / ContentGrid / Connection_
3. Create a connection using all the information provided for the integration.
4. Access the menu _Settings / Technical / ContentGrid / Configuration_
5. Create a configuration using the model you want to use to send attachments to
   contentgrid and specify the correct connection

## Configuration YAML

In order to make the configuration, you need to specify a complex yaml. We will provide
an example and explain the logic of it.

    attachment:
      data:
        name: record.name
        checksum: record.checksum
      binary:
        data:
          compute: record.datas
          name: record.name
          mimetype: record.mimetype
    invoice:
      compute: record
      data:
        name: record.name
        invoice_date: parse_date(record.invoice_date)
        reference: record.ref
      link:
        - attachment
    partner:
      compute: record.partner_id
      data:
        name: record.name
        vat: record.vat
      link:
        - invoice

Each element of the yaml specifies a model in ContentGrid. It must be the same name that
the model has in ContentGrid.

On each element we can the following elements:

- `data`: Specifies a map of simple fields. This must return a dictionaries where the
  key is the name of the field on contentgrid and the value the calculation in odoo for
  the element.
- `binary`: Specifies a map of binary fields. It must return a dictionary where the key
  is the name of the field and the value a new dictionary
  - `compute`: specifies how to compute the base64 data of the file
  - `name`: Specifies the name of the file
  - `mimetype`: Specifies the mimetype of the file
- `compute`: Specifies how to compute the record related to the model. If it is not
  specified, it uses the attachment, otherwise, record is the record related to the
  attachment. All the fields and binary fields will be computed from the record element
  that we have in hands.
- `link`: Specifies a list of relations. It is used to make a relation between elements
  in ContentGrid.

In the example provided:

- `attachment` is a model in ContentGrid that will be filled directly from the
  attachment. It will contain 3 fields, name (`attachment.name`), checksum
  (`attachment.checksum`) and data. Data will be taken directly from the attachment.
- `invoice` corresponds to the related invoice. It corresponds to the related record to
  the attachment (`compute: record`). It has 3 fields: name, invoice_date (parsed with
  parse_date) and reference (`record.ref`). It will be linked to the attachment
- `partner` corresponds to the partner of the invoice (`compute: record.partner_id`). It
  has 2 fields, name and vat. It is linked with the invoice.

If we create a similar configuration with the same connection but for purchase orders,
data will be shown properly in ContentGrid. It means that if we send data for a Purchase
Order and later on the invoice, we will see the invoice and purchase order related to
the same partner.
