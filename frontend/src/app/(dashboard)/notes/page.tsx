"use client";

import { QueryError } from "@/components/query-error";
import { NotebookPen, Plus, Trash2 } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { useCreateNote, useDeleteNote, useNotes, useUpdateNote } from "@/hooks/use-notes";
import { formatDate } from "@/lib/utils";

function NewNoteDialog() {
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [tags, setTags] = useState("");
  const createNote = useCreateNote();

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="gradient">
          <Plus className="h-4 w-4" /> New note
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>New Research Note</DialogTitle>
        </DialogHeader>
        <form
          className="space-y-3"
          onSubmit={(e) => {
            e.preventDefault();
            if (!title.trim()) return;
            createNote.mutate(
              {
                title,
                content,
                tags: tags
                  .split(",")
                  .map((t) => t.trim())
                  .filter(Boolean),
              },
              {
                onSuccess: () => {
                  setOpen(false);
                  setTitle("");
                  setContent("");
                  setTags("");
                },
              },
            );
          }}
        >
          <div className="space-y-1.5">
            <Label>Title</Label>
            <Input value={title} onChange={(e) => setTitle(e.target.value)} autoFocus />
          </div>
          <div className="space-y-1.5">
            <Label>Content</Label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={5}
              className="w-full rounded-lg border border-input bg-background/50 p-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="What did you observe? What would you try next?"
            />
          </div>
          <div className="space-y-1.5">
            <Label>Tags (comma-separated)</Label>
            <Input value={tags} onChange={(e) => setTags(e.target.value)} placeholder="momentum, mean-reversion" />
          </div>
          <DialogFooter>
            <Button type="submit" variant="gradient" disabled={createNote.isPending}>
              Save note
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export default function NotesPage() {
  const { data, isLoading, isError, error, refetch } = useNotes(1, 50);
  const updateNote = useUpdateNote();
  const deleteNote = useDeleteNote();
  const [editingId, setEditingId] = useState<number | null>(null);
  const [draft, setDraft] = useState("");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Research notes</h2>
          <p className="text-sm text-muted-foreground">
            Annotate experiments, compare strategies, and write up findings.
          </p>
        </div>
        <NewNoteDialog />
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-48 w-full rounded-2xl" />
          ))}
        </div>
      ) : isError ? (
        <QueryError error={error} onRetry={() => refetch()} what="your notes" />
      ) : !data || data.items.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-border py-16 text-center">
          <NotebookPen className="h-8 w-8 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">No notes yet. Capture your first research observation.</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data.items.map((note) => (
            <Card key={note.id} className="flex flex-col">
              <CardHeader className="flex-row items-start justify-between space-y-0">
                <div>
                  <p className="font-semibold">{note.title}</p>
                  <p className="text-xs text-muted-foreground">Updated {formatDate(note.updated_at)}</p>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 text-muted-foreground hover:text-destructive"
                  aria-label={`Delete note ${note.title}`}
                  onClick={() => {
                    if (confirm(`Delete the note "${note.title}"? This can't be undone.`)) deleteNote.mutate(note.id);
                  }}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              </CardHeader>
              <CardContent className="flex flex-1 flex-col gap-3">
                {editingId === note.id ? (
                  <textarea
                    className="flex-1 rounded-lg border border-input bg-background/50 p-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    rows={5}
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    onBlur={() => {
                      updateNote.mutate({ id: note.id, content: draft });
                      setEditingId(null);
                    }}
                    autoFocus
                  />
                ) : (
                  <p
                    className="flex-1 cursor-text whitespace-pre-wrap text-sm text-muted-foreground"
                    onClick={() => {
                      setEditingId(note.id);
                      setDraft(note.content);
                    }}
                  >
                    {note.content || "Click to add notes..."}
                  </p>
                )}
                {note.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {note.tags.map((tag) => (
                      <span key={tag} className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
