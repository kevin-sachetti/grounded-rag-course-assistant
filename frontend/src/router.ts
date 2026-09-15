import { createRouter, createWebHistory } from "vue-router";
import ChatView from "./views/ChatView.vue";
import CourseView from "./views/CourseView.vue";
import CoursesView from "./views/CoursesView.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", component: CoursesView },
    { path: "/courses/:id", component: CourseView, props: true },
    { path: "/courses/:id/chat", component: ChatView, props: true },
  ],
});
