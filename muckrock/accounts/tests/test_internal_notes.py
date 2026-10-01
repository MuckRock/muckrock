"""
Tests for internal staff notes about users

Internal notes must never be visible to non-staff users.
"""

# Django
from django.test import TestCase
from django.urls import reverse

# MuckRock
from muckrock.accounts.models import InternalNote
from muckrock.accounts.utils import note_form_prefix
from muckrock.core.factories import UserFactory
from muckrock.foia.factories import FOIAComposerFactory, FOIARequestFactory
from muckrock.task.factories import FlaggedTaskFactory
from muckrock.task.models import MultiRequestTask

NOTE_TEXT = "This user keeps filing the same request over and over"


class InternalNoteTestCase(TestCase):
    """Common set up - a user with a note about them, written by staff"""

    def setUp(self):
        self.staff = UserFactory(is_staff=True)
        self.user = UserFactory()
        self.note = InternalNote.objects.create(
            user=self.user, by=self.staff, text=NOTE_TEXT
        )

    def add_data(self, user, **kwargs):
        """Post data for the add note form, with its form prefix"""
        prefix = note_form_prefix(user=user)
        data = {"text": NOTE_TEXT, **kwargs}
        return {"{}-{}".format(prefix, key): value for key, value in data.items()}

    def edit_data(self, note, **kwargs):
        """Post data for a note's edit form, with its form prefix"""
        prefix = note_form_prefix(note=note)
        data = {"text": NOTE_TEXT, **kwargs}
        return {"{}-{}".format(prefix, key): value for key, value in data.items()}


class TestProfileNotes(InternalNoteTestCase):
    """Notes show up on a user's profile page, for staff only"""

    def setUp(self):
        super().setUp()
        # a submitted composer makes the profile page publicly viewable
        FOIAComposerFactory(user=self.user, status="submitted")
        self.url = reverse("acct-profile", kwargs={"username": self.user.username})

    def test_staff_sees_notes(self):
        """Staff see the notes and the form to add more"""
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        assert response.status_code == 200
        self.assertContains(response, "Internal Notes")
        self.assertContains(response, NOTE_TEXT)
        self.assertContains(
            response, reverse("acct-note-create", kwargs={"idx": self.user.pk})
        )

    def test_note_text_is_markdown(self):
        """Notes are written in markdown"""
        self.note.text = "Filed **too many** requests, see [the log](/foia/)"
        self.note.save()
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        self.assertContains(response, "<strong>too many</strong>")
        self.assertContains(response, '<a href="/foia/">the log</a>')

    def test_note_markdown_is_sanitized(self):
        """Markdown does not let a note smuggle in a script tag"""
        self.note.text = "Suspicious <script>alert('xss')</script>"
        self.note.save()
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        self.assertNotContains(response, "<script>alert")

    def test_owner_does_not_see_notes(self):
        """The user a note is about may never see it"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        assert response.status_code == 200
        self.assertNotContains(response, "Internal Notes")
        self.assertNotContains(response, NOTE_TEXT)

    def test_other_user_does_not_see_notes(self):
        """Other logged in users may not see notes"""
        self.client.force_login(UserFactory())
        response = self.client.get(self.url)
        assert response.status_code == 200
        self.assertNotContains(response, "Internal Notes")
        self.assertNotContains(response, NOTE_TEXT)

    def test_anonymous_does_not_see_notes(self):
        """Logged out users may not see notes"""
        response = self.client.get(self.url)
        assert response.status_code == 200
        self.assertNotContains(response, "Internal Notes")
        self.assertNotContains(response, NOTE_TEXT)


class TestComposerNotes(InternalNoteTestCase):
    """Notes about the filer show up on a multirequest page, for staff only"""

    def setUp(self):
        super().setUp()
        self.composer = FOIAComposerFactory(user=self.user, status="filed")
        # the detail page redirects to the request itself if there is only one
        FOIARequestFactory(composer=self.composer)
        FOIARequestFactory(composer=self.composer)
        self.url = reverse(
            "foia-composer-detail",
            kwargs={"slug": self.composer.slug, "idx": self.composer.pk},
        )

    def test_staff_sees_notes(self):
        """Staff see notes about the user who filed the multirequest"""
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        assert response.status_code == 200
        self.assertContains(response, "Internal Notes")
        self.assertContains(response, NOTE_TEXT)

    def test_owner_does_not_see_notes(self):
        """The filer may not see notes about themselves"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        assert response.status_code == 200
        self.assertNotContains(response, "Internal Notes")
        self.assertNotContains(response, NOTE_TEXT)

    def test_anonymous_does_not_see_notes(self):
        """Logged out users may not see notes"""
        response = self.client.get(self.url)
        assert response.status_code == 200
        self.assertNotContains(response, "Internal Notes")
        self.assertNotContains(response, NOTE_TEXT)


class TestMultiRequestTaskNotes(InternalNoteTestCase):
    """Notes show up on the multirequest task page, which is staff only"""

    def setUp(self):
        super().setUp()
        self.composer = FOIAComposerFactory(user=self.user, status="submitted")
        self.task = MultiRequestTask.objects.create(composer=self.composer)
        self.url = reverse("multirequest-task", kwargs={"pk": self.task.pk})

    def test_staff_sees_notes(self):
        """Staff see notes about the user who filed the multirequest"""
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        assert response.status_code == 200
        self.assertContains(response, "Internal Notes")
        self.assertContains(response, NOTE_TEXT)

    def test_non_staff_cannot_view_the_page(self):
        """The task page itself is staff only"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        assert response.status_code == 302

    def test_task_notes_are_named_apart_from_internal_notes(self):
        """Notes about the request are labeled separately from notes about
        the user, since both forms are on this page"""
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        self.assertContains(response, "Task Notes")
        self.assertContains(response, "Internal Notes")

    def test_other_tasks_still_say_note(self):
        """Only the multirequest page renames the shared note form"""
        self.client.force_login(self.staff)
        flagged = FlaggedTaskFactory()
        response = self.client.get(reverse("flagged-task", kwargs={"pk": flagged.pk}))
        self.assertContains(response, ">Note</p>")
        self.assertNotContains(response, "Task Notes")


class TestCreateNote(InternalNoteTestCase):
    """Only staff may write notes"""

    def setUp(self):
        super().setUp()
        self.url = reverse("acct-note-create", kwargs={"idx": self.user.pk})
        self.profile_url = reverse(
            "acct-profile", kwargs={"username": self.user.username}
        )

    def test_staff_creates_note(self):
        """A staff member's note is credited to them"""
        self.client.force_login(self.staff)
        response = self.client.post(
            self.url, self.add_data(self.user, text="A brand new note")
        )
        assert response.status_code == 302
        assert response.url == self.profile_url
        note = self.user.internal_notes.latest()
        assert note.text == "A brand new note"
        assert note.by == self.staff

    def test_returns_to_the_page_it_came_from(self):
        """Notes can be written from several pages"""
        self.client.force_login(self.staff)
        data = self.add_data(self.user)
        data["next"] = "/task/multirequest/"
        response = self.client.post(self.url, data)
        assert response.status_code == 302
        assert response.url == "/task/multirequest/"

    def test_ignores_offsite_redirects(self):
        """An offsite next falls back to the user's profile"""
        self.client.force_login(self.staff)
        data = self.add_data(self.user)
        data["next"] = "https://example.com/"
        response = self.client.post(self.url, data)
        assert response.status_code == 302
        assert response.url == self.profile_url

    def test_empty_note_is_not_saved(self):
        """The text of a note is required"""
        self.client.force_login(self.staff)
        response = self.client.post(self.url, self.add_data(self.user, text=""))
        assert response.status_code == 302
        assert self.user.internal_notes.count() == 1

    def test_non_staff_cannot_create_note(self):
        """Non-staff users may not write notes"""
        self.client.force_login(self.user)
        response = self.client.post(self.url, self.add_data(self.user))
        assert response.status_code == 302
        assert response.url != self.profile_url
        assert self.user.internal_notes.count() == 1

    def test_anonymous_cannot_create_note(self):
        """Logged out users may not write notes"""
        response = self.client.post(self.url, self.add_data(self.user))
        assert response.status_code == 302
        assert self.user.internal_notes.count() == 1

    def test_get_not_allowed(self):
        """Notes are only written by posting"""
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        assert response.status_code == 405


class TestUpdateNote(InternalNoteTestCase):
    """Only staff may edit notes"""

    def setUp(self):
        super().setUp()
        self.url = reverse("acct-note-update", kwargs={"idx": self.note.pk})

    def test_staff_updates_note(self):
        """Staff can edit a note, including notes they did not write"""
        other_staff = UserFactory(is_staff=True)
        self.client.force_login(other_staff)
        response = self.client.post(
            self.url, self.edit_data(self.note, text="Updated text")
        )
        assert response.status_code == 302
        self.note.refresh_from_db()
        assert self.note.text == "Updated text"
        # the original author is preserved
        assert self.note.by == self.staff

    def test_staff_sets_warning_level(self):
        """Staff can escalate a note's warning level"""
        self.client.force_login(self.staff)
        self.client.post(self.url, self.edit_data(self.note, warning_level="final"))
        self.note.refresh_from_db()
        assert self.note.warning_level == "final"

    def test_non_staff_cannot_update_note(self):
        """Non-staff users may not edit notes"""
        self.client.force_login(self.user)
        response = self.client.post(
            self.url, self.edit_data(self.note, text="Nothing to see here")
        )
        assert response.status_code == 302
        self.note.refresh_from_db()
        assert self.note.text == NOTE_TEXT

    def test_anonymous_cannot_update_note(self):
        """Logged out users may not edit notes"""
        response = self.client.post(
            self.url, self.edit_data(self.note, text="Nothing to see here")
        )
        assert response.status_code == 302
        self.note.refresh_from_db()
        assert self.note.text == NOTE_TEXT


class TestDeleteNote(InternalNoteTestCase):
    """Only staff may delete notes"""

    def setUp(self):
        super().setUp()
        self.url = reverse("acct-note-delete", kwargs={"idx": self.note.pk})

    def test_staff_deletes_note(self):
        """Staff can delete a note"""
        self.client.force_login(self.staff)
        response = self.client.post(self.url)
        assert response.status_code == 302
        assert not InternalNote.objects.filter(pk=self.note.pk).exists()

    def test_non_staff_cannot_delete_note(self):
        """Non-staff users may not delete notes"""
        self.client.force_login(self.user)
        response = self.client.post(self.url)
        assert response.status_code == 302
        assert InternalNote.objects.filter(pk=self.note.pk).exists()

    def test_anonymous_cannot_delete_note(self):
        """Logged out users may not delete notes"""
        response = self.client.post(self.url)
        assert response.status_code == 302
        assert InternalNote.objects.filter(pk=self.note.pk).exists()
