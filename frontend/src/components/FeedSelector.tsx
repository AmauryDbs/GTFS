import * as Select from "@radix-ui/react-select";
import { ChevronDownIcon } from "@radix-ui/react-icons";

interface FeedSelectorProps {
  feeds: Array<{ feed_id: string; provider?: string }>;
  value?: string;
  onChange?: (value?: string) => void;
  placeholder?: string;
}

const itemClass =
  "flex cursor-pointer select-none items-center justify-between rounded px-2 py-1 text-sm text-slate-100 data-[highlighted]:bg-slate-800";

function FeedSelector({ feeds, value, onChange, placeholder }: FeedSelectorProps) {
  return (
    <Select.Root value={value} onValueChange={(next) => onChange?.(next || undefined)}>
      <Select.Trigger className="flex items-center gap-2 rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 shadow-sm">
        <Select.Value placeholder={placeholder ?? "Feed"} />
        <Select.Icon>
          <ChevronDownIcon />
        </Select.Icon>
      </Select.Trigger>
      <Select.Portal>
        <Select.Content className="w-60 rounded-md border border-slate-800 bg-slate-950 p-1 shadow-lg">
          <Select.Viewport>
            {feeds.map((feed) => (
              <Select.Item key={feed.feed_id} value={feed.feed_id} className={itemClass}>
                <Select.ItemText>{feed.provider ?? feed.feed_id}</Select.ItemText>
              </Select.Item>
            ))}
          </Select.Viewport>
        </Select.Content>
      </Select.Portal>
    </Select.Root>
  );
}

export default FeedSelector;
