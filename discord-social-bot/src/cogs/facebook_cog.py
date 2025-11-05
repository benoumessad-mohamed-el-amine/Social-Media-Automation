import discord
from discord.ext import commands
from ..services.facebook import FacebookAPI
import logging

logger = logging.getLogger(__name__)

class FacebookCog(commands.Cog):
    """Discord commands for Facebook operations."""

    def __init__(self, bot):
        self.bot = bot
        self.fb = None  # FacebookAPI instance

    @commands.command(name="fbinit")
    async def fb_init(self, ctx, token: str):
        """Initialize Facebook API with a token."""
        self.fb = FacebookAPI(access_token=token)
        await ctx.send("✅ Facebook API initialized with your access token.")

    @commands.command(name="fbpost")
    async def fb_post(self, ctx, *, message: str):
        """Post text to Facebook."""
        if not self.fb:
            return await ctx.send("❌ Use `/fbinit <token>` first.")
        result = self.fb.post_text(message)
        await ctx.send("✅ Posted!" if result["success"] else f"⚠️ Failed: {result['error']}")

    @commands.command(name="fbposts")
    async def fb_get_posts(self, ctx, limit: int = 5):
        """Fetch recent Facebook posts."""
        if not self.fb:
            return await ctx.send("❌ Initialize the Facebook API first.")
        result = self.fb.get_posts(limit)
        if not result["success"]:
            return await ctx.send(f"⚠️ Error: {result['error']}")
        posts = result["data"].get("data", [])
        if not posts:
            return await ctx.send("📭 No recent posts found.")
        msg = "\n\n".join([f"🆔 `{p['id']}`\n📝 {p.get('message', '(no message)')}" for p in posts])
        await ctx.send(f"📘 **Recent Posts:**\n{msg}")

    @commands.command(name="fbstats")
    async def fb_get_stats(self, ctx, post_id: str):
        """Get stats for a specific Facebook post."""
        if not self.fb:
            return await ctx.send("❌ Initialize first.")
        result = self.fb.get_post_stats(post_id)
        if result["success"]:
            d = result["data"]
            likes = d.get("likes", {}).get("summary", {}).get("total_count", 0)
            comments = d.get("comments", {}).get("summary", {}).get("total_count", 0)
            shares = d.get("shares", {}).get("count", 0)
            await ctx.send(f"📊 **Post Stats:**\n❤️ Likes: {likes}\n💬 Comments: {comments}\n🔁 Shares: {shares}")
        else:
            await ctx.send(f"⚠️ Failed to fetch stats: {result['error']}")

    @commands.command(name="fbreply")
    async def fb_auto_reply(self, ctx, post_id: str, keyword: str, *, reply_text: str):
        """Auto-reply to comments containing a keyword."""
        if not self.fb:
            return await ctx.send("❌ Initialize first.")
        result = self.fb.get_comments(post_id)
        if not result["success"]:
            return await ctx.send(f"⚠️ Failed to fetch comments: {result['error']}")
        matched = 0
        for c in result["data"].get("data", []):
            if keyword.lower() in c.get("message", "").lower():
                self.fb.reply_to_comment(c["id"], reply_text)
                matched += 1
        await ctx.send(f"✅ Auto-replied to {matched} comment(s) containing '{keyword}'.")

    @commands.command(name="fbmoderate")
    async def fb_moderate(self, ctx, comment_id: str, action: str):
        """Moderate a comment (hide/delete)."""
        if not self.fb:
            return await ctx.send("❌ Initialize first.")
        if action.lower() == "hide":
            result = self.fb.hide_comment(comment_id)
        elif action.lower() == "delete":
            result = self.fb.delete_comment(comment_id)
        else:
            return await ctx.send("⚠️ Invalid action. Use 'hide' or 'delete'.")
        if result["success"]:
            await ctx.send(f"✅ Comment {action}d successfully.")
        else:
            await ctx.send(f"⚠️ Failed to {action} comment: {result['error']}")

async def setup(bot):
    await bot.add_cog(FacebookCog(bot))
