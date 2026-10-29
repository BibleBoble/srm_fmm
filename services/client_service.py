"""
Business service for client operations
"""
from datetime import date

class ClientService:
    """
    Service for client operations
    """

    def __init__(self, clients_mgr, contact_persons_mgr, contact_emails_mgr, interactions_mgr):
        self.clients_mgr = clients_mgr
        self.contact_persons_mgr = contact_persons_mgr
        self.contact_emails_mgr = contact_emails_mgr
        self.interactions_mgr = interactions_mgr

    def create_client_with_contacts(self, client_data):
        """
        Create client with contacts
        """
        # Validation
        company = client_data.get('company', '').strip()
        if not company:
            raise ValueError("Company name is required")

        contacts = client_data.get('contacts', [])
        if not contacts:
            raise ValueError("At least one contact is required")

        # Create client
        client_fields = {
            "company": company,
            "address": client_data.get('address', '').strip(),
            "notes": client_data.get('notes', '').strip()
        }
        partner_data = self._get_partner_data(client_data)
        if partner_data is not None:
            client_fields["partner_data"] = partner_data
        client_id = self.clients_mgr.add(**client_fields)

        if not client_id:
            raise RuntimeError("Failed to create client in DB")

        # Add contacts
        for contact in contacts:
            full_name = contact.get('full_name', '').strip()
            if not full_name:
                continue

            contact_id = self.contact_persons_mgr.add(
                client_id=client_id,
                full_name=full_name,
                position=contact.get('position', '').strip(),
                phone=contact.get('phone', '').strip(),
                is_primary=bool(contact.get('is_primary', False))
            )

            # Email
            email = contact.get('email', '').strip()
            if email and contact_id:
                try:
                    self.contact_emails_mgr.add(
                        contact_person_id=contact_id,
                        email=email,
                        is_primary=bool(contact.get('is_primary', False))
                    )
                except Exception as e:
                    print(f"Warning: failed to add email {email}: {e}")

        # History
        try:
            from datetime import date
            self.interactions_mgr.add(
                client_id=client_id,
                date=date.today(),
                type_interaction="Creation",
                description=f"Client added. Contacts: {len(contacts)}"
            )
        except Exception as e:
            print(f"Warning: failed to add history: {e}")

        return client_id

    def update_client_with_contacts(self, client_id, client_data):
        """
        Update client and contacts
        """
        company = client_data.get('company', '').strip()
        if not company:
            raise ValueError("Company name is required")

        client_fields = {
            "company": company,
            "address": client_data.get('address', '').strip(),
            "notes": client_data.get('notes', '').strip()
        }
        partner_data = self._get_partner_data(client_data)
        if partner_data is not None:
            client_fields["partner_data"] = partner_data
        self.clients_mgr.update(client_id, **client_fields)

        if 'contacts' not in client_data:
            return True

        existing_contacts = {
            contact['id']: dict(contact)
            for contact in self.contact_persons_mgr.get_by_client(client_id)
        }
        contacts = [
            contact for contact in client_data.get('contacts', [])
            if contact.get('full_name', '').strip()
        ]
        if not any(contact.get('is_primary') for contact in contacts) and contacts:
            contacts[0]['is_primary'] = True

        retained_ids = set()
        for contact in contacts:
            contact_id = contact.get('id')
            if contact_id is not None:
                try:
                    contact_id = int(contact_id)
                except (TypeError, ValueError) as error:
                    raise ValueError("Некорректный идентификатор контакта") from error
                if contact_id not in existing_contacts:
                    raise ValueError("Контакт не принадлежит этому клиенту")
                self.contact_persons_mgr.update(
                    contact_id,
                    full_name=contact['full_name'].strip(),
                    position=contact.get('position', '').strip(),
                    phone=contact.get('phone', '').strip(),
                    is_primary=bool(contact.get('is_primary'))
                )
            else:
                contact_id = self.contact_persons_mgr.add(
                    client_id=client_id,
                    full_name=contact['full_name'].strip(),
                    position=contact.get('position', '').strip(),
                    phone=contact.get('phone', '').strip(),
                    is_primary=bool(contact.get('is_primary'))
                )
                if not contact_id:
                    raise RuntimeError("Не удалось сохранить контакт клиента")

            retained_ids.add(contact_id)
            if 'email' in contact:
                self._save_primary_email(contact_id, contact.get('email', '').strip())

        for existing_id in existing_contacts:
            if existing_id not in retained_ids:
                self.contact_persons_mgr.delete(existing_id)

        return True

    @staticmethod
    def _get_partner_data(client_data):
        """Return persisted partner-card fields from client form data."""
        partner_fields = (
            'full_legal_name',
            'legal_address',
            'postal_address',
            'ogrn',
            'inn_kpp',
            'bank_details',
            'responsible_person',
            'partner_email',
            'partner_phone'
        )
        if not any(field in client_data for field in partner_fields):
            return None
        return {
            field: str(client_data.get(field) or '').strip()
            for field in partner_fields
        }

    def _save_primary_email(self, contact_id, email):
        """Create, update, or remove the contact's primary email."""
        if not self.contact_emails_mgr:
            if email:
                raise RuntimeError("Менеджер электронной почты не инициализирован")
            return

        emails = self.contact_emails_mgr.get_by_contact(contact_id)
        primary_email = next(
            (item for item in emails if item.get('is_primary')),
            None
        )

        if email:
            if primary_email:
                self.contact_emails_mgr.update(
                    primary_email['id'],
                    email,
                    True
                )
            else:
                self.contact_emails_mgr.add(contact_id, email, is_primary=True)
        elif primary_email:
            self.contact_emails_mgr.delete(primary_email['id'])

    def delete_client(self, client_id):
        """Delete client"""
        try:
            self.clients_mgr.delete(client_id)
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to delete client: {e}")
