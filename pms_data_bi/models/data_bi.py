##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2018 -2023 Alda Hotels <informatica@aldahotels.com>
#                       Jose Luis Algara <osotranquilo@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import ftplib
import json
import logging
import tempfile
from datetime import date, datetime, timedelta

from odoo import api, models

_logger = logging.getLogger(__name__)
estado_array = [
    "draft",
    "confirm",
    "onboard",
    "done",
    "cancel",
    "arrival_delayed",
    "departure_delayed",
]


class DataBi(models.Model):
    """Management and export data for MopSolution MyDataBI."""

    _name = "data_bi"
    _description = "Export DataBI"

    @api.model
    def export_reservations_data(self, hotelsdata=[0], fechafoto=False):
        limit_ago = self.calc_date_limit(fechafoto)
        hotels = self.calc_hoteles(hotelsdata)
        _logger.info("Exporting Reservations data Hotels IDs %s", hotels.ids)
        response = []
        for hotel in hotels:
            response.append(self.export_one(hotel, limit_ago, 6))
            response.append(self.export_one(hotel, limit_ago, 7))
            response.append(self.export_one(hotel, limit_ago, 9))
            response.append(self.export_one(hotel, limit_ago, 10))
        return json.dumps(response, ensure_ascii=False)

    @api.model
    def export_general_data(self, default_property=False):
        _logger.info("Exporting General data DataBI")
        response = []
        dic_hotel = []
        hotel = False
        propertys = self.env["pms.property"].sudo().search([])
        for prop in propertys:
            dic_hotel.append({"ID_Hotel": prop.id, "Descripción": prop.name})
            if prop.id == default_property:
                hotel = prop
        response.append({"Hotel": dic_hotel})
        if not hotel:
            hotel = propertys

        metodos = [
            [self.data_bi_tarifa, "Tarifa"],
            [self.data_bi_canal, "Canal"],
            [self.data_bi_pais, "Pais"],
            [self.data_bi_regimen, "Regimen"],
            [self.data_bi_moti_bloq, "Motivo Bloqueo"],
            [self.data_bi_segment, "Segmentos"],
            [self.data_bi_client, "Clientes"],
            [self.data_bi_habitacione, "Tipo Habitación"],
            [self.data_bi_estados, "Estado Reservas"],
        ]
        for meto in metodos:
            response.append({meto[1]: self.clean_hotel_ids(meto[0]())})
        response.append({"Nombre Habitaciones": self.data_bi_rooms()})
        return json.dumps(response, ensure_ascii=False)

    @api.model
    def calc_hoteles(self, hotelsdata):
        if hotelsdata != [0]:
            hotels = self.env["pms.property"].search(
                [("id", "in", hotelsdata), ("status_send_property", "=", True)]
            )
        else:
            hotels = self.env["pms.property"].search(
                [("status_send_property", "=", True)]
            )
        return hotels

    @api.model
    def calc_date_limit(self, fechafoto):
        if not fechafoto:
            fechafoto = date.today().strftime("%Y-%m-%d")
        if type(fechafoto) is dict:
            fechafoto = date.today()
        else:
            fechafoto = datetime.strptime(fechafoto, "%Y-%m-%d").date()
        dias = self.env.user.data_bi_days
        limit_ago = (fechafoto - timedelta(days=dias)).strftime("%Y-%m-%d")
        _logger.info("Export Data %s days ago. From %s", dias, limit_ago)
        return limit_ago

    @api.model
    def clean_hotel_ids(self, datadict):
        for da in datadict:
            da.pop("ID_Hotel", None)
        return datadict

    @api.model
    def export_data_bi(self, archivo=0, default_property=[0], fechafoto=False):
        """Prepare a Json Objet to export data for MyDataBI.

        Generate a dicctionary to by send in JSON
        archivo = response file type
            archivo == 0 'ALL'
            archivo == 1 'Tarifa'
            archivo == 2 'Canal'
            archivo == 3 'Hotel'
            archivo == 4 'Pais'
            archivo == 5 'Regimen'
            archivo == 6 'Reservas'
            archivo == 7 'Capacidad'
            archivo == 8 'Tipo Habitación'
            archivo == 9 'Budget'
            archivo == 10 'Bloqueos'
            archivo == 11 'Motivo Bloqueo'
            archivo == 12 'Segmentos'
            archivo == 13 'Clientes'
            archivo == 14 'Estado Reservas'
            archivo == 15 'Room names'
        fechafoto = start date to take data
        """
        limit_ago = self.calc_date_limit(fechafoto)
        hotels = self.calc_hoteles(default_property)

        _logger.info(
            "-- ### Init Export Data_Bi Module parameters:  %s, %s, %s ### --",
            archivo,
            hotels.ids,
            fechafoto,
        )

        if archivo == 0:
            dic_export = self.export_all(hotels, limit_ago)
        else:
            dic_export = self.export_one(hotels, limit_ago, archivo)

        _logger.info("--- ### End Export Data_Bi Module to Json ### ---")
        return json.dumps(dic_export, ensure_ascii=False)

    @api.model
    def export_all(self, hotels, limit_ago):
        line_res = self.env["pms.reservation.line"].search(
            [("pms_property_id", "in", hotels.ids), ("date", ">=", limit_ago)],
            order="id",
        )
        dic_reservas = self.data_bi_reservas(
            hotels,
            line_res,
            estado_array,
        )
        dic_export = [
            {"Tarifa": self.data_bi_tarifa(hotels)},
            {"Canal": self.data_bi_canal(hotels)},
            {"Hotel": self.data_bi_hotel()},
            {"Pais": self.data_bi_pais(hotels)},
            {"Regimen": self.data_bi_regimen(hotels)},
            {"Reservas": dic_reservas},
            {"Capacidad": self.data_bi_capacidad(hotels)},
            {"Tipo Habitación": self.data_bi_habitacione(hotels)},
            {"Budget": self.data_bi_budget(hotels)},
            {"Bloqueos": self.data_bi_bloqueos(hotels, line_res)},
            {"Motivo Bloqueo": self.data_bi_moti_bloq(hotels)},
            {"Segmentos": self.data_bi_segment(hotels)},
            {"Clientes": self.data_bi_client(hotels)},
            {"Estado Reservas": self.data_bi_estados(hotels)},
            {"Nombre Habitaciones": self.data_bi_rooms(hotels)},
        ]
        return dic_export

    @api.model
    def export_one(self, hotels, limit_ago, archivo):
        if (archivo == 0) or (archivo == 10) or (archivo == 6):
            line_res = self.env["pms.reservation.line"].search(
                [("pms_property_id", "in", hotels.ids), ("date", ">=", limit_ago)],
                order="id",
            )
            dic_reservas = self.data_bi_reservas(
                hotels,
                line_res,
                estado_array,
            )
        dic_export = []
        if archivo == 1:
            dic_export.append({"Tarifa": self.data_bi_tarifa(hotels)})
        elif archivo == 2:
            dic_export.append({"Canal": self.data_bi_canal(hotels)})
        elif archivo == 3:
            dic_export.append({"Hotel": self.data_bi_hotel()})
        elif archivo == 4:
            dic_export.append({"Pais": self.data_bi_pais(hotels)})
        elif archivo == 5:
            dic_export.append({"Regimen": self.data_bi_regimen(hotels)})
        elif archivo == 6:
            dic_export.append({"Reservas": dic_reservas})
        elif archivo == 7:
            dic_export.append({"Capacidad": self.data_bi_capacidad(hotels)})
        elif archivo == 8:
            dic_export.append({"Tipo Habitación": self.data_bi_habitacione(hotels)})
        elif archivo == 9:
            dic_export.append({"Budget": self.data_bi_budget(hotels)})
        elif archivo == 10:
            dic_export.append({"Bloqueos": self.data_bi_bloqueos(hotels, line_res)})
        elif archivo == 11:
            dic_export.append({"Motivo Bloqueo": self.data_bi_moti_bloq(hotels)})
        elif archivo == 12:
            dic_export.append({"Segmentos": self.data_bi_segment(hotels)})
        elif archivo == 13:
            dic_export.append({"Clientes": self.data_bi_client(hotels)})
        elif archivo == 14:
            dic_export.append({"Estado Reservas": self.data_bi_estados(hotels)})
        elif archivo == 15:
            dic_export.append({"Nombre Habitaciones": self.data_bi_rooms(hotels)})
        return dic_export

    @api.model
    def data_bi_tarifa(self, hotels=False):
        # Diccionario con las tarifas [1]
        dic_tarifa = []
        if not hotels:
            hotels = self.env["pms.property"].sudo().search([])

        tarifas = (
            self.env["product.pricelist"]
            .sudo()
            .search(
                [
                    "|",
                    ("active", "=", False),
                    ("active", "=", True),
                ]
            )
            .filtered(
                lambda r: not r.pms_property_ids
                or any([p.id in hotels.ids for p in r.pms_property_ids])
            )
        )
        for tarifa in tarifas:
            dic_tarifa.append(
                {
                    "ID_Hotel": hotels[0].id,
                    "ID_Tarifa": tarifa["id"],
                    "Descripción": tarifa["name"],
                }
            )
        return dic_tarifa

    @api.model
    def data_bi_canal(self, hotels=False):
        # Diccionario con los Canales [2]
        dic_canal = []
        if not hotels:
            hotels = self.env["pms.property"].sudo().search([])
        channels = (
            self.env["pms.sale.channel"]
            .sudo()
            .search([])
            .filtered(
                lambda r: not r.pms_property_ids
                or any([p.id in hotels.ids for p in r.pms_property_ids])
            )
        )
        # _logger.info("DataBi: Calculating %s Channels", str(len(channels)))
        dic_canal.append(
            {"ID_Hotel": hotels[0].id, "ID_Canal": 0, "Descripción": "Ninguno"}
        )
        for channel in channels:
            dic_canal.append(
                {
                    "ID_Hotel": hotels[0].id,
                    "ID_Canal": channel["id"],
                    "Descripción": channel["name"],
                }
            )
        return dic_canal

    @api.model
    def data_bi_hotel(self):
        # Diccionario con el/los nombre de los hoteles  [3]
        hoteles = self.env["pms.property"].search([])
        # _logger.info("DataBi: Calculating %s hotel names", str(len(hoteles)))

        dic_hotel = []
        for hotel in hoteles:
            dic_hotel.append({"ID_Hotel": hotel.id, "Descripción": hotel.name})
        return dic_hotel

    @api.model
    def data_bi_pais(self, hotels=False):
        dic_pais = []
        if not hotels:
            hotels = self.env["pms.property"].sudo().search([], limit=1)
        dic_ine = [
            {"ID_Pais": "NONE", "Descripción": "No Asignado"},
            {"ID_Pais": "AFG", "Descripción": "Afganistán"},
            {"ID_Pais": "ALB", "Descripción": "Albania"},
            {"ID_Pais": "DEU", "Descripción": "Alemania"},
            {"ID_Pais": "AND", "Descripción": "Andorra"},
            {"ID_Pais": "AGO", "Descripción": "Angola"},
            {"ID_Pais": "AIA", "Descripción": "Anguila"},
            {"ID_Pais": "ATG", "Descripción": "Antigua y Barbuda"},
            {"ID_Pais": "ANT", "Descripción": "Antillas Neerlandesas"},
            {"ID_Pais": "ATA", "Descripción": "Antártida"},
            {"ID_Pais": "SAU", "Descripción": "Arabia Saudita"},
            {"ID_Pais": "DZA", "Descripción": "Argelia"},
            {"ID_Pais": "ARG", "Descripción": "Argentina"},
            {"ID_Pais": "ARM", "Descripción": "Armenia"},
            {"ID_Pais": "ABW", "Descripción": "Aruba"},
            {"ID_Pais": "AUS", "Descripción": "Australia"},
            {"ID_Pais": "AUT", "Descripción": "Austria"},
            {"ID_Pais": "AZE", "Descripción": "Azerbaiyán"},
            {"ID_Pais": "BHS", "Descripción": "Bahamas"},
            {"ID_Pais": "BHR", "Descripción": "Bahrein"},
            {"ID_Pais": "BGD", "Descripción": "Bangladesh"},
            {"ID_Pais": "BRB", "Descripción": "Barbados"},
            {"ID_Pais": "BLZ", "Descripción": "Belice"},
            {"ID_Pais": "BEN", "Descripción": "Benin"},
            {"ID_Pais": "BMU", "Descripción": "Bermudas"},
            {"ID_Pais": "BTN", "Descripción": "Bhután"},
            {"ID_Pais": "BLR", "Descripción": "Bielorrusia"},
            {"ID_Pais": "BOL", "Descripción": "Bolivia"},
            {"ID_Pais": "BIH", "Descripción": "Bosnia-Herzegovina"},
            {"ID_Pais": "BWA", "Descripción": "Botswana"},
            {"ID_Pais": "BRA", "Descripción": "Brasil"},
            {"ID_Pais": "BRN", "Descripción": "Brunéi"},
            {"ID_Pais": "BGR", "Descripción": "Bulgaria"},
            {"ID_Pais": "BFA", "Descripción": "Burkina Fasso"},
            {"ID_Pais": "BDI", "Descripción": "Burundi"},
            {"ID_Pais": "BEL", "Descripción": "Bélgica"},
            {"ID_Pais": "CPV", "Descripción": "Cabo Verde"},
            {"ID_Pais": "KHM", "Descripción": "Camboya"},
            {"ID_Pais": "CMR", "Descripción": "Camerún"},
            {"ID_Pais": "CAN", "Descripción": "Canadá"},
            {"ID_Pais": "TCD", "Descripción": "Chad"},
            {"ID_Pais": "CHL", "Descripción": "Chile"},
            {"ID_Pais": "CHN", "Descripción": "China"},
            {"ID_Pais": "CYP", "Descripción": "Chipre"},
            {"ID_Pais": "COL", "Descripción": "Colombia"},
            {"ID_Pais": "COM", "Descripción": "Comoras"},
            {"ID_Pais": "COG", "Descripción": "Congo, República del"},
            {"ID_Pais": "COD", "Descripción": "Congo, República Democrática del"},
            {"ID_Pais": "PRK", "Descripción": "Corea, Rep. Popular Democrática"},
            {"ID_Pais": "KOR", "Descripción": "Corea, República de"},
            {"ID_Pais": "CIV", "Descripción": "Costa de Marfil"},
            {"ID_Pais": "CRI", "Descripción": "Costa Rica"},
            {"ID_Pais": "HRV", "Descripción": "Croacia"},
            {"ID_Pais": "CUB", "Descripción": "Cuba"},
            {"ID_Pais": "DNK", "Descripción": "Dinamarca"},
            {"ID_Pais": "DMA", "Descripción": "Dominica"},
            {"ID_Pais": "ECU", "Descripción": "Ecuador"},
            {"ID_Pais": "EGY", "Descripción": "Egipto"},
            {"ID_Pais": "SLV", "Descripción": "El Salvador"},
            {"ID_Pais": "ARE", "Descripción": "Emiratos Arabes Unidos"},
            {"ID_Pais": "ERI", "Descripción": "Eritrea"},
            {"ID_Pais": "SVK", "Descripción": "Eslovaquia"},
            {"ID_Pais": "SVN", "Descripción": "Eslovenia"},
            {"ID_Pais": "USA", "Descripción": "Estados Unidos de América"},
            {"ID_Pais": "EST", "Descripción": "Estonia"},
            {"ID_Pais": "ETH", "Descripción": "Etiopía"},
            {"ID_Pais": "PHL", "Descripción": "Filipinas"},
            {"ID_Pais": "FIN", "Descripción": "Finlandia"},
            {"ID_Pais": "FRA", "Descripción": "Francia"},
            {"ID_Pais": "GAB", "Descripción": "Gabón"},
            {"ID_Pais": "GMB", "Descripción": "Gambia"},
            {"ID_Pais": "GEO", "Descripción": "Georgia"},
            {"ID_Pais": "GHA", "Descripción": "Ghana"},
            {"ID_Pais": "GIB", "Descripción": "Gibraltar"},
            {"ID_Pais": "GRD", "Descripción": "Granada"},
            {"ID_Pais": "GRC", "Descripción": "Grecia"},
            {"ID_Pais": "GRL", "Descripción": "Groenlandia"},
            {"ID_Pais": "GLP", "Descripción": "Guadalupe"},
            {"ID_Pais": "GUM", "Descripción": "Guam"},
            {"ID_Pais": "GTM", "Descripción": "Guatemala"},
            {"ID_Pais": "GUF", "Descripción": "Guayana Francesa"},
            {"ID_Pais": "GIN", "Descripción": "Guinea"},
            {"ID_Pais": "GNQ", "Descripción": "Guinea Ecuatorial"},
            {"ID_Pais": "GNB", "Descripción": "Guinea-Bissau"},
            {"ID_Pais": "GUY", "Descripción": "Guyana"},
            {"ID_Pais": "HTI", "Descripción": "Haití"},
            {"ID_Pais": "HND", "Descripción": "Honduras"},
            {"ID_Pais": "HKG", "Descripción": "Hong-Kong"},
            {"ID_Pais": "HUN", "Descripción": "Hungría"},
            {"ID_Pais": "IND", "Descripción": "India"},
            {"ID_Pais": "IDN", "Descripción": "Indonesia"},
            {"ID_Pais": "IRQ", "Descripción": "Irak"},
            {"ID_Pais": "IRL", "Descripción": "Irlanda"},
            {"ID_Pais": "IRN", "Descripción": "Irán"},
            {"ID_Pais": "BVT", "Descripción": "Isla Bouvert"},
            {"ID_Pais": "GGY", "Descripción": "Isla de Guernesey"},
            {"ID_Pais": "JEY", "Descripción": "Isla de Jersey"},
            {"ID_Pais": "IMN", "Descripción": "Isla de Man"},
            {"ID_Pais": "CXR", "Descripción": "Isla de Navidad"},
            {"ID_Pais": "ISL", "Descripción": "Islandia"},
            {"ID_Pais": "CYM", "Descripción": "Islas Caimán"},
            {"ID_Pais": "CCK", "Descripción": "Islas Cocos"},
            {"ID_Pais": "COK", "Descripción": "Islas Cook"},
            {"ID_Pais": "FLK", "Descripción": "Islas Falkland (Malvinas)"},
            {"ID_Pais": "FRO", "Descripción": "Islas Feroé"},
            {"ID_Pais": "FJI", "Descripción": "Islas Fidji"},
            {"ID_Pais": "SGS", "Descripción": "Islas Georgias del Sur y Sandwich"},
            {"ID_Pais": "HMD", "Descripción": "Islas Heard e Mcdonald"},
            {"ID_Pais": "MNP", "Descripción": "Islas Marianas del Norte"},
            {"ID_Pais": "MHL", "Descripción": "Islas Marshall"},
            {"ID_Pais": "UMI", "Descripción": "Islas Menores de EEUU"},
            {"ID_Pais": "NFK", "Descripción": "Islas Norfolk"},
            {"ID_Pais": "PCN", "Descripción": "Islas Pitcairn"},
            {"ID_Pais": "SLB", "Descripción": "Islas Salomón"},
            {"ID_Pais": "TCA", "Descripción": "Islas Turcas y Caicos"},
            {"ID_Pais": "VGB", "Descripción": "Islas Vírgenes Británicas"},
            {"ID_Pais": "VIR", "Descripción": "Islas Vírgenes de los EEUU"},
            {"ID_Pais": "WLF", "Descripción": "Islas Wallis y Futura"},
            {"ID_Pais": "ALA", "Descripción": "Islas Åland"},
            {"ID_Pais": "ISR", "Descripción": "Israel"},
            {"ID_Pais": "ITA", "Descripción": "Italia"},
            {"ID_Pais": "JAM", "Descripción": "Jamaica"},
            {"ID_Pais": "JPN", "Descripción": "Japón"},
            {"ID_Pais": "JOR", "Descripción": "Jordania"},
            {"ID_Pais": "KAZ", "Descripción": "Kazajstán"},
            {"ID_Pais": "KEN", "Descripción": "Kenia"},
            {"ID_Pais": "KGZ", "Descripción": "Kirguistán"},
            {"ID_Pais": "KIR", "Descripción": "Kiribati"},
            {"ID_Pais": "KWT", "Descripción": "Kuwait"},
            {"ID_Pais": "LAO", "Descripción": "Laos"},
            {"ID_Pais": "LSO", "Descripción": "Lesotho"},
            {"ID_Pais": "LVA", "Descripción": "Letonia"},
            {"ID_Pais": "LBY", "Descripción": "Libia"},
            {"ID_Pais": "LBR", "Descripción": "Libéria"},
            {"ID_Pais": "LIE", "Descripción": "Liechtenstein"},
            {"ID_Pais": "LTU", "Descripción": "Lituania"},
            {"ID_Pais": "LUX", "Descripción": "Luxemburgo"},
            {"ID_Pais": "LBN", "Descripción": "Líbano"},
            {"ID_Pais": "MAC", "Descripción": "Macao"},
            {"ID_Pais": "MKD", "Descripción": "Macedonia, ARY"},
            {"ID_Pais": "MDG", "Descripción": "Madagascar"},
            {"ID_Pais": "MYS", "Descripción": "Malasia"},
            {"ID_Pais": "MWI", "Descripción": "Malawi"},
            {"ID_Pais": "MDV", "Descripción": "Maldivas"},
            {"ID_Pais": "MLT", "Descripción": "Malta"},
            {"ID_Pais": "MLI", "Descripción": "Malí"},
            {"ID_Pais": "MAR", "Descripción": "Marruecos"},
            {"ID_Pais": "MTQ", "Descripción": "Martinica"},
            {"ID_Pais": "MUS", "Descripción": "Mauricio"},
            {"ID_Pais": "MRT", "Descripción": "Mauritania"},
            {"ID_Pais": "MYT", "Descripción": "Mayotte"},
            {"ID_Pais": "FSM", "Descripción": "Micronesia"},
            {"ID_Pais": "MDA", "Descripción": "Moldavia"},
            {"ID_Pais": "MNG", "Descripción": "Mongolia"},
            {"ID_Pais": "MNE", "Descripción": "Montenegro"},
            {"ID_Pais": "MSR", "Descripción": "Montserrat"},
            {"ID_Pais": "MOZ", "Descripción": "Mozambique"},
            {"ID_Pais": "MMR", "Descripción": "Myanmar"},
            {"ID_Pais": "MEX", "Descripción": "México"},
            {"ID_Pais": "MCO", "Descripción": "Mónaco"},
            {"ID_Pais": "NAM", "Descripción": "Namibia"},
            {"ID_Pais": "NRU", "Descripción": "Naurú"},
            {"ID_Pais": "NPL", "Descripción": "Nepal"},
            {"ID_Pais": "NIC", "Descripción": "Nicaragua"},
            {"ID_Pais": "NGA", "Descripción": "Nigeria"},
            {"ID_Pais": "NIU", "Descripción": "Niue"},
            {"ID_Pais": "NOR", "Descripción": "Noruega"},
            {"ID_Pais": "NCL", "Descripción": "Nueva Caledonia"},
            {"ID_Pais": "NZL", "Descripción": "Nueva Zelanda"},
            {"ID_Pais": "NER", "Descripción": "Níger"},
            {"ID_Pais": "OMN", "Descripción": "Omán"},
            {"ID_Pais": "PAK", "Descripción": "Pakistán"},
            {"ID_Pais": "PLW", "Descripción": "Palau"},
            {"ID_Pais": "PSE", "Descripción": "Palestina, Territorio ocupado"},
            {"ID_Pais": "PAN", "Descripción": "Panamá"},
            {"ID_Pais": "PNG", "Descripción": "Papua Nueva Guinea"},
            {"ID_Pais": "PRY", "Descripción": "Paraguay"},
            {"ID_Pais": "NLD", "Descripción": "Países Bajos"},
            {"ID_Pais": "PER", "Descripción": "Perú"},
            {"ID_Pais": "PYF", "Descripción": "Polinesia Francesa"},
            {"ID_Pais": "POL", "Descripción": "Polonia"},
            {"ID_Pais": "PRT", "Descripción": "Portugal"},
            {"ID_Pais": "PRI", "Descripción": "Puerto Rico"},
            {"ID_Pais": "QAT", "Descripción": "Qatar"},
            {"ID_Pais": "GBR", "Descripción": "Reino Unido"},
            {"ID_Pais": "CAF", "Descripción": "República Centroafricana"},
            {"ID_Pais": "CZE", "Descripción": "República Checa"},
            {"ID_Pais": "DOM", "Descripción": "República Dominicana"},
            {"ID_Pais": "REU", "Descripción": "Reunión"},
            {"ID_Pais": "ROU", "Descripción": "Rumania"},
            {"ID_Pais": "RUS", "Descripción": "Rusia"},
            {"ID_Pais": "RWA", "Descripción": "Rwanda"},
            {"ID_Pais": "ESH", "Descripción": "Sahara Occidental"},
            {"ID_Pais": "KNA", "Descripción": "Saint Kitts y Nevis"},
            {"ID_Pais": "WSM", "Descripción": "Samoa"},
            {"ID_Pais": "ASM", "Descripción": "Samoa Americana"},
            {"ID_Pais": "BLM", "Descripción": "San Bartolomé"},
            {"ID_Pais": "SMR", "Descripción": "San Marino"},
            {"ID_Pais": "MAF", "Descripción": "San Martín"},
            {"ID_Pais": "SPM", "Descripción": "San Pedro y Miquelón"},
            {"ID_Pais": "VCT", "Descripción": "San Vicente y las Granadinas"},
            {"ID_Pais": "SHN", "Descripción": "Santa Elena"},
            {"ID_Pais": "LCA", "Descripción": "Santa Lucía"},
            {"ID_Pais": "STP", "Descripción": "Santo Tomé y Príncipe"},
            {"ID_Pais": "SEN", "Descripción": "Senegal"},
            {"ID_Pais": "SRB", "Descripción": "Serbia"},
            {"ID_Pais": "SYC", "Descripción": "Seychelles"},
            {"ID_Pais": "SLE", "Descripción": "Sierra Leona"},
            {"ID_Pais": "SGP", "Descripción": "Singapur"},
            {"ID_Pais": "SYR", "Descripción": "Siria"},
            {"ID_Pais": "SOM", "Descripción": "Somalia"},
            {"ID_Pais": "LKA", "Descripción": "Sri Lanka"},
            {"ID_Pais": "SWZ", "Descripción": "Suazilandia"},
            {"ID_Pais": "ZAF", "Descripción": "Sudáfrica"},
            {"ID_Pais": "SDN", "Descripción": "Sudán"},
            {"ID_Pais": "SWE", "Descripción": "Suecia"},
            {"ID_Pais": "CHE", "Descripción": "Suiza"},
            {"ID_Pais": "SUR", "Descripción": "Suriname"},
            {"ID_Pais": "SJM", "Descripción": "Svalbard e Islas de Jan Mayen"},
            {"ID_Pais": "THA", "Descripción": "Tailandia"},
            {"ID_Pais": "TWN", "Descripción": "Taiwán"},
            {"ID_Pais": "TZA", "Descripción": "Tanzania"},
            {"ID_Pais": "TJK", "Descripción": "Tayikistan"},
            {"ID_Pais": "IOT", "Descripción": "Terr. Británico del Oc. Indico"},
            {"ID_Pais": "ATF", "Descripción": "Tierras Australes Francesas"},
            {"ID_Pais": "TLS", "Descripción": "Timor Oriental"},
            {"ID_Pais": "TGO", "Descripción": "Togo"},
            {"ID_Pais": "TKL", "Descripción": "Tokelau"},
            {"ID_Pais": "TON", "Descripción": "Tonga"},
            {"ID_Pais": "TTO", "Descripción": "Trinidad y Tobago"},
            {"ID_Pais": "TKM", "Descripción": "Turkmenistán"},
            {"ID_Pais": "TUR", "Descripción": "Turquía"},
            {"ID_Pais": "TUV", "Descripción": "Tuvalu"},
            {"ID_Pais": "TUN", "Descripción": "Túnez"},
            {"ID_Pais": "UKR", "Descripción": "Ucrania"},
            {"ID_Pais": "UGA", "Descripción": "Uganda"},
            {"ID_Pais": "URY", "Descripción": "Uruguay"},
            {"ID_Pais": "UZB", "Descripción": "Uzbekistán"},
            {"ID_Pais": "VUT", "Descripción": "Vanuatu"},
            {"ID_Pais": "VAT", "Descripción": "Vaticano, Santa Sede"},
            {"ID_Pais": "VEN", "Descripción": "Venezuela"},
            {"ID_Pais": "VNM", "Descripción": "Vietnam"},
            {"ID_Pais": "YEM", "Descripción": "Yemen"},
            {"ID_Pais": "DJI", "Descripción": "Yibuti"},
            {"ID_Pais": "ZMB", "Descripción": "Zambia"},
            {"ID_Pais": "ZWE", "Descripción": "Zimbabwe"},
            {"ID_Pais": "KOS", "Descripción": "Kosovo"},
            {"ID_Pais": "ES111", "Descripción": "A Coruña"},
            {"ID_Pais": "ES112", "Descripción": "Lugo"},
            {"ID_Pais": "ES113", "Descripción": "Ourense"},
            {"ID_Pais": "ES114", "Descripción": "Pontevedra"},
            {"ID_Pais": "ES120", "Descripción": "Asturias"},
            {"ID_Pais": "ES130", "Descripción": "Cantabria"},
            {"ID_Pais": "ES211", "Descripción": "Araba/Álava"},
            {"ID_Pais": "ES212", "Descripción": "Gipuzkoa"},
            {"ID_Pais": "ES213", "Descripción": "Bizkaia"},
            {"ID_Pais": "ES220", "Descripción": "Navarra"},
            {"ID_Pais": "ES230", "Descripción": "La Rioja"},
            {"ID_Pais": "ES241", "Descripción": "Huesca"},
            {"ID_Pais": "ES242", "Descripción": "Teruel"},
            {"ID_Pais": "ES243", "Descripción": "Zaragoza"},
            {"ID_Pais": "ES300", "Descripción": "Madrid"},
            {"ID_Pais": "ES411", "Descripción": "Ávila"},
            {"ID_Pais": "ES412", "Descripción": "Burgos"},
            {"ID_Pais": "ES413", "Descripción": "León"},
            {"ID_Pais": "ES414", "Descripción": "Palencia"},
            {"ID_Pais": "ES415", "Descripción": "Salamanca"},
            {"ID_Pais": "ES416", "Descripción": "Segovia"},
            {"ID_Pais": "ES417", "Descripción": "Soria"},
            {"ID_Pais": "ES418", "Descripción": "Valladolid"},
            {"ID_Pais": "ES419", "Descripción": "Zamora"},
            {"ID_Pais": "ES421", "Descripción": "Albacete"},
            {"ID_Pais": "ES422", "Descripción": "Ciudad Real"},
            {"ID_Pais": "ES423", "Descripción": "Cuenca"},
            {"ID_Pais": "ES424", "Descripción": "Guadalajara"},
            {"ID_Pais": "ES425", "Descripción": "Toledo"},
            {"ID_Pais": "ES431", "Descripción": "Badajoz"},
            {"ID_Pais": "ES432", "Descripción": "Cáceres"},
            {"ID_Pais": "ES511", "Descripción": "Barcelona"},
            {"ID_Pais": "ES512", "Descripción": "Girona"},
            {"ID_Pais": "ES513", "Descripción": "Lleida"},
            {"ID_Pais": "ES514", "Descripción": "Tarragona"},
            {"ID_Pais": "ES521", "Descripción": "Alicante / Alacant"},
            {"ID_Pais": "ES522", "Descripción": "Castellón / Castelló"},
            {"ID_Pais": "ES523", "Descripción": "Valencia / Valéncia"},
            {"ID_Pais": "ES530", "Descripción": "Illes Balears"},
            {"ID_Pais": "ES531", "Descripción": "Eivissa y Formentera"},
            {"ID_Pais": "ES532", "Descripción": "Mallorca"},
            {"ID_Pais": "ES533", "Descripción": "Menorca"},
            {"ID_Pais": "ES611", "Descripción": "Almería"},
            {"ID_Pais": "ES612", "Descripción": "Cádiz"},
            {"ID_Pais": "ES613", "Descripción": "Córdoba"},
            {"ID_Pais": "ES614", "Descripción": "Granada"},
            {"ID_Pais": "ES615", "Descripción": "Huelva"},
            {"ID_Pais": "ES616", "Descripción": "Jaén"},
            {"ID_Pais": "ES617", "Descripción": "Málaga"},
            {"ID_Pais": "ES618", "Descripción": "Sevilla"},
            {"ID_Pais": "ES620", "Descripción": "Murcia"},
            {"ID_Pais": "ES630", "Descripción": "Ceuta"},
            {"ID_Pais": "ES640", "Descripción": "Melilla"},
            {"ID_Pais": "ES701", "Descripción": "Las Palmas"},
            {"ID_Pais": "ES702", "Descripción": "Santa Cruz de Tenerife"},
            {"ID_Pais": "ES703", "Descripción": "El Hierro"},
            {"ID_Pais": "ES704", "Descripción": "Fuerteventura"},
            {"ID_Pais": "ES705", "Descripción": "Gran Canaria"},
            {"ID_Pais": "ES706", "Descripción": "La Gomera"},
            {"ID_Pais": "ES707", "Descripción": "La Palma"},
            {"ID_Pais": "ES708", "Descripción": "Lanzarote"},
            {"ID_Pais": "ES709", "Descripción": "Tenerife"},
        ]
        # Diccionario con los nombre de los Paises usando los del INE [4]
        # _logger.info("DataBi: Calculating %s countries", str(len(dic_ine)))
        for prop in hotels:
            for pais in dic_ine:
                dic_pais.append(
                    {
                        "ID_Hotel": prop.id,
                        "ID_Pais": pais["ID_Pais"],
                        "Descripción": pais["Descripción"],
                    }
                )
        return dic_pais

    @api.model
    def data_bi_regimen(self, hotels=False):
        # Diccionario con los Board Services [5]
        dic_regimen = []
        if not hotels:
            hotels = self.env["pms.property"].sudo().search([])
        board_services = (
            self.env["pms.board.service"]
            .sudo()
            .search([])
            .filtered(
                lambda r: not r.pms_property_ids
                or any([p.id in hotels.ids for p in r.pms_property_ids])
            )
        )
        # _logger.info("DataBi: Calculating %s board services",
        dic_regimen.append(
            {
                "ID_Hotel": hotels[0].id,
                "ID_Regimen": 0,
                "Descripción": "Sin régimen",
            }
        )
        for board_service in board_services:
            dic_regimen.append(
                {
                    "ID_Hotel": hotels[0].id,
                    "ID_Regimen": board_service["id"],
                    "Descripción": board_service["name"],
                }
            )
        return dic_regimen

    @api.model
    def data_bi_capacidad(self, hotels):
        # Diccionario con las capacidades  [7]
        rooms_type = self.env["pms.room.type"].search([])
        # _logger.info("DataBi: Calculating %s room capacity", str(len(rooms)))
        dic_capacidad = []
        for prop in hotels:
            for room_type in rooms_type:
                room_count = self.data_bi_get_capacidad(prop.id, room_type.id)
                if room_count > 0:
                    dic_capacidad.append(
                        {
                            "ID_Hotel": prop.id,
                            "Hasta_Fecha": (
                                date.today() + timedelta(days=365 * 3)
                            ).strftime("%Y-%m-%d"),
                            "ID_Tipo_Habitacion": room_type.id,
                            "Nro_Habitaciones": room_count,
                        }
                    )
        return dic_capacidad

    @api.model
    def data_bi_habitacione(self, hotels=False):
        # Diccionario con Rooms types [8]
        if not hotels:
            hotels = self.env["pms.property"].sudo().search([])
        rooms = (
            self.env["pms.room.type"]
            .sudo()
            .search([])
            .filtered(
                lambda r: not r.pms_property_ids
                or any([p.id in hotels.ids for p in r.pms_property_ids])
            )
        )
        # _logger.info("DataBi: Calculating %s room types", str(len(rooms)))
        dic_tipo_habitacion = []
        for room in rooms:
            dic_tipo_habitacion.append(
                {
                    "ID_Hotel": hotels[0].id,
                    "ID_Tipo_Habitacion": room["id"],
                    "Descripción": room["name"],
                    "Estancias": room[0].get_room_type_capacity(hotels[0].id),
                }
            )
        return dic_tipo_habitacion

    @api.model
    def data_bi_budget(self, hotels):
        # Diccionario con las previsiones Budget [9]
        budgets = self.env["pms.budget"].search([])
        # _logger.info("DataBi: Calculating %s budget", str(len(budgets)))
        dic_budget = []
        for prop in hotels:
            for budget in budgets:
                if budget.pms_property_id.id == prop.id:
                    dic_budget.append(
                        {
                            "ID_Hotel": prop.id,
                            "Fecha": (
                                str(budget.year)
                                + "-"
                                + str(budget.month).zfill(2)
                                + "-01"
                            ),
                            # 'ID_Tarifa': 0,
                            # 'ID_Canal': 0,
                            # 'ID_Pais': 0,
                            # 'ID_Regimen': 0,
                            # 'ID_Tipo_Habitacion': 0,
                            # 'ID_Cliente': 0,
                            "Room_Nights": budget.room_nights,
                            "Room_Revenue": budget.room_revenue,
                            # 'Pension_Revenue': 0,
                            "Estancias": budget.estancias,
                        }
                    )
            # Fecha fecha Primer día del mes
            # ID_Tarifa numérico Código de la Tarifa
            # ID_Canal numérico Código del Canal
            # ID_Pais numérico Código del País
            # ID_Regimen numérico Cóigo del Régimen
            # ID_Tipo_Habitacion numérico Código del Tipo de Habitación
            # iD_Segmento numérico Código del Segmento
            # ID_Cliente numérico Código del Cliente
            # Pension_Revenue numérico con dos decimales Ingresos por Pensión
        return dic_budget

    @api.model
    def data_bi_moti_bloq(self, hotels=False):
        # Diccionario con Motivo de Bloqueos [11]
        dic_moti_bloq = []
        if not hotels:
            hotels = self.env["pms.property"].sudo().search([])
        lineas = (
            self.env["room.closure.reason"]
            .sudo()
            .search([])
            .filtered(
                lambda r: not r.pms_property_ids
                or any([p.id in hotels.ids for p in r.pms_property_ids])
            )
        )
        # _logger.info("DataBi: Calculating %s blocking reasons",
        #   str(len(lineas)))
        dic_moti_bloq.append(
            {
                "ID_Hotel": hotels[0].id,
                "ID_Motivo_Bloqueo": "B0",
                "Descripción": "Ninguno",
            }
        )
        dic_moti_bloq.append(
            {
                "ID_Hotel": hotels[0].id,
                "ID_Motivo_Bloqueo": "ST",
                "Descripción": "Staff",
            }
        )
        for linea in lineas:
            dic_moti_bloq.append(
                {
                    "ID_Hotel": hotels[0].id,
                    "ID_Motivo_Bloqueo": "B" + str(linea.id),
                    "Descripción": linea.name,
                }
            )
        return dic_moti_bloq

    @api.model
    def data_bi_segment(self, hotels=False):
        # Diccionario con Segmentación [12]
        dic_segmentos = []
        if not hotels:
            hotels = self.env["pms.property"].sudo().search([])
        lineas = self.env["res.partner.category"].sudo().search([])
        # _logger.info("DataBi: Calculating %s segmentations", str(len(lineas)))
        for linea in lineas:
            if linea.parent_id.name:
                seg_desc = linea.parent_id.name + " / " + linea.name
            else:
                seg_desc = linea.name
            dic_segmentos.append(
                {
                    "ID_Hotel": hotels[0].id,
                    "ID_Segmento": linea.id,
                    "Descripción": seg_desc,
                }
            )
        return dic_segmentos

    @api.model
    def data_bi_client(self, hotels=False):
        # Diccionario con Clientes (OTAs y agencias) [13]
        dic_clientes = []
        if not hotels:
            hotels = self.env["pms.property"].sudo().search([])
        lineas = (
            self.env["res.partner"]
            .sudo()
            .search([("is_agency", "=", True)])
            .filtered(
                lambda r: not r.pms_property_ids
                or any([p.id in hotels.ids for p in r.pms_property_ids])
            )
        )
        # _logger.info("DataBi: Calculating %s Operators", str(len(lineas)))
        dic_clientes.append(
            {"ID_Hotel": hotels[0].id, "ID_Cliente": 0, "Descripción": "Ninguno"}
        )
        for linea in lineas:
            dic_clientes.append(
                {
                    "ID_Hotel": hotels[0].id,
                    "ID_Cliente": linea.id,
                    "Descripción": linea.data_bi_ref
                    if linea.data_bi_ref
                    else linea.name,
                }
            )
        return dic_clientes

    @api.model
    def data_bi_estados(self, hotels=False):
        # Diccionario con los Estados Reserva [14]
        # _logger.info("DataBi: Calculating states of the reserves")
        if not hotels:
            hotels = self.env["pms.property"].sudo().search([])
        dic_estados = []
        estado_array_txt = [
            "Borrador",
            "Confirmada",
            "Hospedandose",
            "Checkout",
            "Cancelada",
            "No Show",
            "No Checkout",
        ]
        for i in range(0, len(estado_array)):
            dic_estados.append(
                {
                    "ID_Hotel": hotels[0].id,
                    "ID_EstadoReserva": str(i),
                    "Descripción": estado_array_txt[i],
                }
            )
        return dic_estados

    @api.model
    def data_bi_rooms(self, hotels=False):
        # Diccionario con las habitaciones [15]
        dic_rooms = []
        if not hotels:
            hotels = self.env["pms.property"].sudo().search([])
        rooms = (
            self.env["pms.room"]
            .sudo()
            .search([])
            .filtered(
                lambda r: not r.pms_property_id
                or any([p.id in hotels.ids for p in r.pms_property_id])
            )
        )
        # _logger.info("DataBi: Calculating %s name rooms.", str(len(rooms)))
        for room in rooms:
            dic_rooms.append(
                {
                    "ID_Hotel": room.pms_property_id.id,
                    "ID_Room": room.id,
                    "Descripción": room.name,
                }
            )
        return dic_rooms

    @api.model
    def data_bi_bloqueos(self, hotels, lines):
        # Diccionario con Bloqueos [10]
        dic_bloqueos = []
        lines = lines.filtered(
            lambda n: (
                (n.reservation_id.reservation_type != "normal")
                and (n.reservation_id.state != "cancel")
            )
        )
        # _logger.info("DataBi: Calculating %s Bloqued", str(len(lines)))
        for line in lines:

            if line.pms_property_id.id in hotels.ids:
                motivo = "0"
                if line.reservation_id.reservation_type == "out":
                    motivo = (
                        "B0"
                        if not line.reservation_id.closure_reason_id.id
                        else ("B" + str(line.reservation_id.closure_reason_id.id))
                    )

                elif line.reservation_id.reservation_type == "staff":
                    motivo = "ST"
                dic_bloqueos.append(
                    {
                        "ID_Hotel": line.pms_property_id.id,
                        "Fecha_desde": line.date.strftime("%Y-%m-%d"),
                        "Fecha_hasta": (line.date + timedelta(days=1)).strftime(
                            "%Y-%m-%d"
                        ),
                        "ID_Tipo_Habitacion": line.reservation_id.room_type_id.id,
                        "ID_Motivo_Bloqueo": motivo,
                        "Nro_Habitaciones": 1,
                    }
                )
        return dic_bloqueos

    @api.model
    def data_bi_reservas(self, hotels, lines, estado_array):
        # Diccionario con Reservas  [6]
        dic_reservas = []

        for prop in hotels:
            lineas = lines.filtered(
                lambda n: (
                    (n.pms_property_id.id == prop.id)
                    and (n.reservation_id.reservation_type == "normal")
                )
                # and (n.price > 0)
            )
            # _logger.info(
            #     "DataBi: Calculating %s reservations in %s ",
            #     str(len(lineas)),
            #     prop.name,
            # )

            for linea in lineas:
                if linea.reservation_id.segmentation_ids:
                    id_segmen = linea.reservation_id.segmentation_ids[0].id
                elif linea.reservation_id.folio_id.segmentation_ids:
                    id_segmen = linea.reservation_id.folio_id.segmentation_ids[0].id
                else:
                    id_segmen = 0

                regimen = (
                    0
                    if not linea.reservation_id.board_service_room_id
                    else linea.reservation_id.board_service_room_id.id
                )

                cuna = 0
                for service in linea.reservation_id.service_ids:
                    if service.product_id.is_crib:
                        cuna += 1

                canal = (
                    linea.reservation_id.sale_channel_origin_id.id
                    if linea.reservation_id.sale_channel_origin_id.id
                    else 0
                )

                cliente = (
                    linea.reservation_id.agency_id.id
                    if linea.reservation_id.agency_id.id
                    else 0
                )
                cliente = canal if cliente == 0 else cliente

                precio_comision = round(
                    linea.reservation_id.commission_amount
                    / len(linea.reservation_id.reservation_line_ids),
                    2,
                )
                precio_iva = 0
                for iva in linea.reservation_id.tax_ids:
                    precio_iva += round(iva.amount * linea.price / 100, 2)

                dic_reservas.append(
                    {
                        "ID_Reserva": linea.reservation_id.id,
                        "ID_Hotel": prop.id,
                        "ID_EstadoReserva": estado_array.index(
                            linea.reservation_id.state
                        ),
                        "FechaVenta": linea.reservation_id.create_date.strftime(
                            "%Y-%m-%d"
                        ),
                        "ID_Segmento": id_segmen,
                        "ID_Cliente": cliente,
                        "ID_Canal": canal,
                        "FechaExtraccion": date.today().strftime("%Y-%m-%d"),
                        "Entrada": linea.date.strftime("%Y-%m-%d"),
                        "Salida": (linea.date + timedelta(days=1)).strftime("%Y-%m-%d"),
                        "Noches": 1,
                        "ID_TipoHabitacion": linea.reservation_id.room_type_id.id,
                        "ID_HabitacionDuerme": linea.room_id.room_type_id.id,
                        "ID_Regimen": regimen,
                        "Adultos": linea.reservation_id.adults,
                        "Menores": linea.reservation_id.children,
                        "Cunas": cuna,
                        "PrecioDiario": linea.price - precio_comision - precio_iva,
                        "PrecioDto": linea.discount * (linea.price / 100),
                        "PrecioComision": precio_comision,
                        "PrecioIva": precio_iva,
                        "ID_Tarifa": linea.reservation_id.pricelist_id.id,
                        "ID_Pais": self.data_bi_get_codeine(linea),
                        "ID_Room": linea.room_id.id,
                        "FechaCancelacion": "NONE",
                        "ID_Folio": linea.reservation_id.folio_id.name,
                    }
                )

                if linea.reservation_id.state == "cancel":
                    dic_reservas[-1][
                        "FechaCancelacion"
                    ] = linea.reservation_id.write_date.strftime("%Y-%m-%d")

                # ID_Reserva numérico Código único de la reserva
                # ID_Hotel numérico Código del Hotel
                # ID_EstadoReserva numérico Código del estado de la reserva
                # FechaVenta fecha Fecha de la venta de la reserva
                # ID_Segmento numérico Código del Segmento de la reserva
                # ID_Cliente Numérico Código del Cliente de la reserva
                # ID_Canal numérico Código del Canal
                # FechaExtraccion fecha Fecha de la extracción de los datos (Foto)
                # Entrada fecha Fecha de entrada
                # Salida fecha Fecha de salida
                # Noches numérico Nro. de noches de la reserva
                # ID_TipoHabitacion numérico Código del Tipo de Habitación
                # ID_Regimen numérico Código del Tipo de Régimen
                # Adultos numérico Nro. de adultos
                # Menores numérico Nro. de menores
                # Cunas numérico Nro. de cunas
                # PrecioDiario numérico con 2 decimales Precio por noche de la reserva
                # ID_Tarifa numérico Código de la tarifa aplicada a la reserva
                # ID_Pais alfanumérico Código del país

        return dic_reservas

    @api.model
    def data_bi_get_codeine(self, reserva):
        response = "NONE"
        if reserva.reservation_id.partner_id.ine_code:
            response = reserva.reservation_id.partner_id.ine_code
        else:
            for partner in reserva.reservation_id.checkin_partner_ids:
                if partner.partner_id.ine_code:
                    response = partner.partner_id.ine_code
        return response

    @api.model
    def data_bi_get_capacidad(self, prop, rtype):
        rooms = self.env["pms.room"].search(
            [("pms_property_id", "=", prop), ("room_type_id", "=", rtype)]
        )
        return len(rooms)

    @api.model
    def data_bi_ftp_general(self):
        """send DataBI general data to ftp server"""
        _logger.info("Exporting FTP general DataBI")
        self.data_bi_ftp_write(
            self.export_general_data(), self.env.user.maestro_ftp_bi , "MaestraV3/"
        )
        return

    @api.model
    def data_bi_ftp(self, default_property=[0], fechafoto=False):
        """send DataBI from all property to ftp server
        default_property is a list of propertys ids
        example: default_property = [1,4,5]
        for all not set or default_property = [0]
        """
        _logger.info("Exporting FTP data DataBI")
        # propertys = self.env["pms.property"].search([])
        propertys = self.env["pms.property"].search(
            [("status_send_property", "=", True)]
        )
        for prop in propertys:
            if (prop.id in default_property) or default_property == [0]:
                self.data_bi_ftp_one(prop, fechafoto)
            self.invalidate_cache()
        return

    @api.model
    def data_bi_ftp_one(self, prop, fechafoto):
        """send 1 DataBI to ftp server"""
        data = json.dumps(
            self.export_all(prop, self.calc_date_limit(fechafoto)), ensure_ascii=False
        )
        filename = (
            "BI"
            + str(prop.id)
            + "-"
            + (prop.pms_property_code if prop.pms_property_code else "00")
        )
        _logger.info("Send to ftp " + filename)
        self.data_bi_ftp_write(data, filename)
        return

    @api.model
    def data_bi_ftp_write(self, data, file, directory="/"):
        if not self.env.user.valid_ftp_bi:
            _logger.error("FTP data not validated in user")
            _logger.error(self.env.user.name)
            return
        try:
            with ftplib.FTP(
                host=self.env.user.url_ftp_bi,
                user=self.env.user.user_ftp_bi,
                passwd=self.env.user.pass_ftp_bi,
            ) as ftp:
                tfile = tempfile.NamedTemporaryFile("w+b")
                tfile.write(bytes(data, "utf-8"))
                tfile.flush()
                tfile.seek(0)
                ftpResponseMessage = ftp.storbinary(
                    "STOR " + directory + file + ".json", tfile
                )
                _logger.warning(ftpResponseMessage)
                ftp.close()
                tfile.close()
        except ftplib.all_errors as e:
            _logger.error("%s" % e)
