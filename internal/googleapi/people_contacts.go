package googleapi

import (
	"context"
	"fmt"

	"github.com/vinitkumar/googlecl/internal/model"
)

// ListContacts reads saved contacts, not directory users or implicit other contacts.
func (c *Client) ListContacts(ctx context.Context) ([]model.Contact, error) {
	result := []model.Contact{}
	token := ""
	for page := 0; page < maxPages; page++ {
		response, err := c.people.People.Connections.List("people/me").PersonFields("names,emailAddresses,phoneNumbers").PageSize(1000).PageToken(token).SortOrder("FIRST_NAME_ASCENDING").Context(ctx).Do()
		if err != nil {
			return nil, fmt.Errorf("list People contacts: %w", err)
		}
		for _, person := range response.Connections {
			contact := model.Contact{ID: person.ResourceName, Emails: []string{}, Phones: []string{}}
			if len(person.Names) > 0 {
				contact.Name = person.Names[0].DisplayName
			}
			for _, email := range person.EmailAddresses {
				contact.Emails = append(contact.Emails, email.Value)
			}
			for _, phone := range person.PhoneNumbers {
				contact.Phones = append(contact.Phones, phone.Value)
			}
			result = append(result, contact)
		}
		if response.NextPageToken == "" {
			return result, nil
		}
		token = response.NextPageToken
	}
	return nil, fmt.Errorf("People pagination exceeded %d pages", maxPages)
}
