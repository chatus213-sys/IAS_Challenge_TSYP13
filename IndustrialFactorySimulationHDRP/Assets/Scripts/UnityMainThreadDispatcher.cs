using System;
using System.Collections.Generic;
using UnityEngine;

public class UnityMainThreadDispatcher : MonoBehaviour
{
    private static readonly Queue<Action> ExecutionQueue = new Queue<Action>();

    void Update()
    {
        lock (ExecutionQueue)
        {
            while (ExecutionQueue.Count > 0)
            {
                ExecutionQueue.Dequeue()?.Invoke();
            }
        }
    }

    public static void Enqueue(Action action)
    {
        lock (ExecutionQueue)
        {
            ExecutionQueue.Enqueue(action);
        }
    }
}
