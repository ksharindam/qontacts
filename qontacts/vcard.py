# -*- coding: utf-8 -*-
# This file is a part of Qontacts Program which is GNU GPLv3 licensed
# Copyright (C) 2026 Arindam Chaudhuri <arindamsoft94@gmail.com>
import base64
import quopri


class Contact:
    phone_types = ["Phone", "Email", "Jio", "Vi", "Airtel"]
    def __init__(self, name="", phones=None):
        self.name = name
        self.phones = phones or {}
        self.emails = []
        self.photo = None # jpeg data in python bytes.


class vCard:
    """ supports reading v2.1 and v3.0 of vCard file. writes only 3.0 """
    def read_file(self, filename):
        lines = []
        with open(filename, "r", encoding='utf-8') as f:
            for line in f:
                line = line.rstrip()
                if not line:
                    continue
                if line.startswith(" ") or line.startswith("\t"):# wrapped line
                    lines[-1] = lines[-1] + line[1:]
                else:
                    lines.append(line)

        contacts = []
        contact = None
        for i,line in enumerate(lines):
            if line.startswith("BEGIN:VCARD"):
                contact = Contact()
            elif line.startswith("END:VCARD"):
                if contact and (contact.phones or contact.emails):
                    contacts.append(contact)
                contact = None
            elif line.startswith("VERSION:"):
                self.version = line[8:]
            else:
                if self.version=="2.1":
                    self.read_v2(line, contact)
                elif self.version=="3.0":
                    self.read_v3(line, contact)
        return contacts

    def read_v3(self, line, contact):
        """ default v3.0 format (most compatible).
        For specifications see https://www.rfc-editor.org/info/rfc2426/"""
        prop, val = line.split(":", maxsplit=1)
        # formatted name
        if prop.startswith("FN"):
            # eg. FN:Arindam Chaudhuri
            contact.name = val
        elif prop.startswith("TEL"):
            # eg. TEL;TYPE=cell,pref:0123456789
            if val in contact.phones:# duplicate
                return
            typ = "Phone"
            pref = False
            params = self.parse_property(prop)
            for type in params["TYPE"]:# tel-type (cell, home, work, pref ...) case-insensitive
                if type.lower().startswith("x-"):
                    if (custom_typ:=type[2:]) in Contact.phone_types:
                        typ = custom_typ
                elif type.lower()=="pref":
                    pref = True
            if pref:
                contact.phones = {val:typ} | contact.phones # add to beginning
            else:
                contact.phones[val] = typ

        elif prop.startswith("EMAIL"):# email-type (internet, x400)
            # eg. EMAIL;TYPE=internet,pref:arindam@example.com
            if val not in contact.emails:
                contact.emails.append(val)
        elif prop.startswith("PHOTO"):
            # eg. PHOTO;ENCODING=b;TYPE=jpeg:<base64_encoded_data>
            contact.photo = base64.b64decode(val)
            # base64 encoded data uri has format "data:image/jpeg;base64,<endcoded_data>"


    def read_v2(self, line, contact):
        """ legacy v2.1 format """
        prop, val = line.split(":", maxsplit=1)
        # formatted name
        if prop.startswith("FN"):
            # eg. FN:Arindam Chaudhuri
            # or FN;CHARSET=UTF-8;ENCODING=QUOTED-PRINTABLE:<encoded_name>
            if "ENCODING=QUOTED-PRINTABLE" in prop:
                val = quopri.decodestring(val.encode()).decode()
            contact.name = val
        elif prop.startswith("TEL"):
            # eg. TEL;CELL;PREF:+0123456789
            if val in contact.phones:# duplicate
                return
            typ = "Phone"
            params = prop.split(";")[1:]
            if params and params[0].startswith("X-"):
                if (custom_typ:=params[0][2:]) in Contact.phone_types:
                    typ = custom_typ
            if "PREF" in params:
                contact.phones = {val:typ} | contact.phones # add to beginning
            else:
                contact.phones[val] = typ
        elif prop.startswith("EMAIL"):
            # eg. EMAIL;PREF;HOME:arindam@example.com
            if val not in contact.emails:
                contact.emails.append(val)
        elif prop.startswith("PHOTO"):
            # eg. PHOTO;ENCODING=BASE64;JPEG:<encoded data>
            contact.photo = base64.b64decode(val)


    def parse_property(self, prop):
        """ parse "TEL;TYPE=cell,pref" into {"TYPE": ["cell","pref"]} """
        prop_parts = prop.split(";")# property_name;param1;param2...
        params = {}
        for param in prop_parts[1:]:# eg. TYPE=cell,home,pref
            key, val = param.split("=")
            params[key] = val.split(",")# multiple property values are separated by comma
        # property name, parameters, value
        return params


    def write_file(self, filename, contacts):
        for contact in contacts:
            self.write_contact(filename, contact)

    def write_contact(self, filename, contact):
        """ write contact in v3.0 format """
        with open(filename, "a", encoding='utf-8', newline="\r\n") as f:
            f.write("BEGIN:VCARD\nVERSION:3.0\n")
            # Structured Name <LastName; FirstName; AdditionalName; Prefix; Suffix>
            parts = contact.name.split(" ")
            first_name = parts[0]
            last_name = parts[-1] if len(parts)>1 else ""
            middle_name = " ".join(parts[1:-1]) if len(parts)>2 else ""
            self.write_line(f, f"N:{last_name};{first_name};{middle_name};;")
            # Formatted Name
            self.write_line(f, "FN:%s" % contact.name)
            # phone number
            for i, phone in enumerate(contact.phones.items()):
                number, typ = phone
                typ = "cell" if typ=="Phone" else "X-"+typ
                pref = ",pref" if (len(contact.phones)>1 and i==0) else ""
                self.write_line(f, "TEL;TYPE=%s%s:%s" % (typ, pref, number))
            # email
            for email in contact.emails:
                self.write_line(f, f"EMAIL;TYPE=internet:{email}")
            # contact photo
            if contact.photo:
                data = base64.b64encode(contact.photo).decode()
                self.write_line(f, f"PHOTO;ENCODING=b;TYPE=jpeg:{data}")
            f.write("END:VCARD\n")

    def write_line(self, f, line):
        """ line must not have newline character """
        size = len(line)
        end = min(75, size)
        f.write(line[:end] + "\n")
        begin = end
        # wrap line so that each line contains maximum 75 chars including leading space
        while begin<size:
            end = min(begin+74, size)
            f.write(" " + line[begin:end] + "\n")
            begin = end
